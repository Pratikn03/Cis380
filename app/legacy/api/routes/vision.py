"""
==============================================================================
VISION API ROUTE - Image Classification & Real/Fake Detection
==============================================================================
Author: Pratik Niroula
Project: Sentifargo (Sentifargo)

WHAT THIS FILE DOES:
--------------------
This file provides API endpoints for computer vision tasks:

1. /api/vision/train - Train image classification models
2. /api/vision/predict - Classify single images (real vs fake)
3. /api/vision/classify-image - Alternative classification endpoint
4. /api/vision/classify-video - Analyze video frames
5. /api/vision/batch - Batch process multiple images

MAIN USE CASE:
--------------
Detecting FAKE (manipulated/AI-generated) vs REAL images.
This is useful for:
- Identifying deepfakes
- Detecting AI-generated images
- Verifying authentic photographs

HOW IMAGE CLASSIFICATION WORKS:
-------------------------------
    Input Image (e.g., photo.jpg)
           │
           ▼
    ┌─────────────────────────────────────┐
    │  Preprocessing                       │
    │  - Resize to 224x224 pixels         │
    │  - Normalize RGB values (0-1)       │
    │  - Apply ImageNet normalization     │
    └─────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────┐
    │  CNN Model (ResNet18)               │
    │  - Extract visual features          │
    │  - Convolution layers detect edges, │
    │    textures, patterns               │
    │  - Fully connected layer outputs    │
    │    class probabilities              │
    └─────────────────────────────────────┘
           │
           ▼
    Output: {"label": "REAL", "confidence": 0.92}

MODEL FILES:
------------
    models/vision/resnet/model.pt     - Trained PyTorch model weights
    models/vision/resnet/classes.txt  - Class names (e.g., "FAKE", "REAL")

SUPPORTED IMAGE FORMATS:
------------------------
    .jpg, .jpeg, .png, .bmp, .gif, .tiff, .webp

API EXAMPLES:
-------------
    # Classify single image
    curl -X POST http://localhost:8000/api/vision/predict \\
         -F "file=@photo.jpg"
    
    # Train new model
    curl -X POST http://localhost:8000/api/vision/train \\
         -H "Content-Type: application/json" \\
         -d '{"dataset_dir": "data/raw/images", "epochs": 10}'
==============================================================================
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import statistics
import shutil
import subprocess
import tempfile

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel, Field

from ..deps import require_auth
from uais.vision.train_vision_model import IMAGE_EXTENSIONS, VisionConfig, run_vision_experiment
from app.utils.uploads import (
    IMAGE_EXTENSIONS as SAFE_IMAGE_EXTENSIONS,
    IMAGE_MIME_TYPES,
    MAX_IMAGE_BYTES,
    MAX_VIDEO_BYTES,
    VIDEO_EXTENSIONS,
    VIDEO_MIME_TYPES,
    read_image_payload,
    read_upload_bytes,
    validate_upload,
)

# ==============================================================================
# ROUTER SETUP
# ==============================================================================
router = APIRouter(prefix="/api/vision", tags=["vision"], dependencies=[Depends(require_auth)])

# Default path to training dataset (Intel Image Classification dataset)
DEFAULT_DATASET = (
    "data/raw/vision/datasets/puneet6060/intel-image-classification/versions/2/seg_train/seg_train"
)


class VisionRequest(BaseModel):
    dataset_dir: str = Field(
        DEFAULT_DATASET,
        description="Relative path to an image classification dataset organized in class folders.",
    )
    run_experiment: bool = Field(
        False,
        description="Set to true to train a quick vision experiment using TensorFlow (may take longer).",
    )
    image_size: int = Field(128, gt=0, description="Height/width to resize images to.")
    batch_size: int = Field(
        32, gt=0, description="Batch size used during training when running experiments."
    )
    epochs: int = Field(
        1, gt=0, description="Number of epochs when running the optional experiment."
    )
    validation_split: float = Field(
        0.2,
        gt=0.0,
        lt=1.0,
        description="Validation split used when running the optional experiment.",
    )
    backbone: str = Field("simple_cnn", description="Backbone model for the optional experiment.")


def _summarize_classes(dataset_root: Path) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for entry in dataset_root.iterdir():
        if not entry.is_dir():
            continue
        class_name = entry.name
        for img in entry.rglob("*"):
            if not img.is_file():
                continue
            if img.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            counts[class_name] += 1
    return dict(counts)


@router.post("/train")
def vision_experiment(req: VisionRequest):
    cfg = VisionConfig(
        dataset_dir=req.dataset_dir,
        image_size=req.image_size,
        batch_size=req.batch_size,
        epochs=req.epochs,
        validation_split=req.validation_split,
        backbone=req.backbone,
    )

    try:
        dataset_root = cfg.resolve_dir()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset directory not found: {req.dataset_dir}",
        ) from exc

    class_summary = _summarize_classes(dataset_root)
    payload = {
        "dataset_root": str(dataset_root),
        "class_counts": class_summary,
        "total_images": sum(class_summary.values()),
        "preview_message": "Vision dataset summary ready. Set run_experiment=true to train a small model.",
    }

    if req.run_experiment:
        try:
            metrics = run_vision_experiment(cfg)
        except Exception as exc:  # pragma: no cover - runtime errors bubbled to caller
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Vision experiment failed: {exc}",
            ) from exc
        payload["metrics"] = metrics
        payload["preview_message"] = "Vision experiment completed successfully."

    return payload


VISION_MODEL_PATH = Path("models/vision/resnet/model.pt")
VISION_CLASSES_PATH = Path("models/vision/resnet/classes.txt")
VISION_DEFAULT_CLASS_DIR = Path("data/processed/vision/train")


def _load_vision_class_names() -> list[str]:
    if VISION_CLASSES_PATH.exists():
        try:
            names = [
                line.strip()
                for line in VISION_CLASSES_PATH.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            if names:
                return names
        except Exception:
            pass
    if VISION_DEFAULT_CLASS_DIR.exists():
        names = sorted([p.name for p in VISION_DEFAULT_CLASS_DIR.iterdir() if p.is_dir()])
        if names:
            return names
    return ["class0", "class1"]


def _load_vision_predictor():
    """Load the ResNet vision model + preprocessing transform (cached)."""
    import functools

    @functools.lru_cache(maxsize=1)
    def _cached():
        try:
            import torch
            from torchvision import transforms
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(f"torch/torchvision not available: {exc}") from exc

        import os

        from uais_v.models.vision_resnet import VisionConfig as ResNetCfg, build_resnet_classifier

        class_names = _load_vision_class_names()
        num_classes = len(class_names)

        device: "torch.device"
        # Default to CPU for maximum portability/stability (MPS can be flaky in some macOS setups).
        # Override with Sentifargo_VISION_DEVICE=cuda|mps|cpu if desired.
        requested = (
            os.getenv("Sentifargo_VISION_DEVICE") or os.getenv("Sentifargo_VISION_DEVICE") or ""
        ).strip().lower()
        if requested:
            device = torch.device(requested)
        else:
            device = torch.device("cpu")

        if not VISION_MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Vision model not found at {VISION_MODEL_PATH}. Train it with: bash scripts/run_train_vision.sh"
            )

        # For inference we load our own checkpoint; disable torchvision pretrained weights
        # to avoid any network downloads and speed up cold starts.
        model = build_resnet_classifier(ResNetCfg(num_classes=num_classes, pretrained=False)).to(
            device
        )
        state = torch.load(VISION_MODEL_PATH, map_location=device)
        model.load_state_dict(state, strict=True)
        model.eval()

        transform = transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )
        return model, transform, class_names, device

    return _cached()


@router.post("/predict")
async def vision_predict(
    file: UploadFile | None = File(default=None),
    image_url: str | None = Form(default=None),
    image_base64: str | None = Form(default=None),
    top_k: int = 3,
):
    """Predict class label for an uploaded image or image_url using the trained ResNet artifact."""
    try:
        import io

        from PIL import Image
        import torch
    except Exception as exc:  # pragma: no cover - optional dependency
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Missing deps: {exc}"
        ) from exc

    try:
        image_bytes = await read_image_payload(
            file=file,
            image_url=image_url,
            image_base64=image_base64,
            allowed_exts=SAFE_IMAGE_EXTENSIONS,
            allowed_mimes=IMAGE_MIME_TYPES,
            max_bytes=MAX_IMAGE_BYTES,
            kind="image",
        )
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid image: {exc}"
        ) from exc

    try:
        model, transform, class_names, device = _load_vision_predictor()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vision model load failed: {exc}",
        ) from exc

    try:
        tensor = transform(image).unsqueeze(0).to(device)
        with torch.no_grad():
            logits = model(tensor)
            probs = torch.softmax(logits, dim=1).detach().cpu().numpy().ravel().tolist()
        if not probs:
            raise RuntimeError("Empty prediction output.")
        top_k = max(1, min(int(top_k), len(probs)))
        ranked = sorted(enumerate(probs), key=lambda x: x[1], reverse=True)[:top_k]
        best_idx, best_prob = ranked[0]
        filename = "image"
        if file is not None and file.filename:
            filename = file.filename
        elif image_url:
            filename = image_url
        elif image_base64:
            filename = "image_base64"
        return {
            "filename": filename,
            "label": (
                class_names[int(best_idx)] if int(best_idx) < len(class_names) else str(best_idx)
            ),
            "confidence": round(float(best_prob), 6),
            "top_k": [
                {
                    "label": class_names[int(i)] if int(i) < len(class_names) else str(i),
                    "prob": round(float(p), 6),
                }
                for i, p in ranked
            ],
            "num_classes": len(class_names),
            "classes": class_names,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vision predict failed: {exc}",
        ) from exc


@router.post("/face_emotion/predict")
async def face_emotion_predict(file: UploadFile = File(...), top_k: int = 3):
    """Predict a 7-class facial emotion label from an uploaded image."""
    validate_upload(
        file,
        allowed_exts=SAFE_IMAGE_EXTENSIONS,
        allowed_mimes=IMAGE_MIME_TYPES,
        max_bytes=MAX_IMAGE_BYTES,
        kind="image",
    )
    try:
        image_bytes = await read_upload_bytes(file, max_bytes=MAX_IMAGE_BYTES, kind="image")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not read upload: {exc}"
        ) from exc

    try:
        from app.models.vision.face_emotion_predict import (
            FaceEmotionModelNotTrainedError,
            predict_face_emotion,
        )

        return predict_face_emotion(image_bytes=image_bytes, filename=file.filename, top_k=top_k)
    except FaceEmotionModelNotTrainedError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Face emotion predict failed: {exc}",
        ) from exc


@router.post("/video/predict")
async def vision_video_predict(
    file: UploadFile = File(...),
    fps: float = 1.0,
    max_frames: int = 30,
    top_k: int = 3,
):
    """Predict for an uploaded video by sampling frames, aggregating probabilities, and scoring temporal-consistency.

    If `models/vision/video_temporal_model.pkl` exists, also returns a learned temporal confidence score
    via `temporal_confidence_model`.
    """
    try:
        from PIL import Image, ImageChops
        import torch
    except Exception as exc:  # pragma: no cover - optional dependency
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Missing deps: {exc}"
        ) from exc

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ffmpeg not found; install ffmpeg or run image-only inference at /api/vision/predict",
        )

    if fps <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="fps must be > 0")
    if max_frames < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="max_frames must be >= 0"
        )

    try:
        model, transform, class_names, device = _load_vision_predictor()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vision model load failed: {exc}",
        ) from exc

    validate_upload(
        file,
        allowed_exts=VIDEO_EXTENSIONS,
        allowed_mimes=VIDEO_MIME_TYPES,
        max_bytes=MAX_VIDEO_BYTES,
        kind="video",
    )
    try:
        video_bytes = await read_upload_bytes(file, max_bytes=MAX_VIDEO_BYTES, kind="video")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not read upload: {exc}"
        ) from exc

    with tempfile.TemporaryDirectory(prefix="Sentifargo_video_") as tmp:
        tmp_dir = Path(tmp)
        video_path = tmp_dir / (Path(file.filename).name if file.filename else "upload.mp4")
        frames_dir = tmp_dir / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)
        try:
            video_path.write_bytes(video_bytes)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Could not write temp file: {exc}",
            ) from exc

        out_pattern = frames_dir / "frame_%06d.jpg"
        cmd = [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(video_path),
            "-vf",
            f"fps={fps}",
        ]
        if max_frames > 0:
            cmd += ["-vframes", str(max_frames)]
        cmd.append(str(out_pattern))

        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"ffmpeg failed to extract frames (is the video valid?): {exc}",
            ) from exc

        frame_paths = sorted(frames_dir.glob("frame_*.jpg"))
        if not frame_paths:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No frames extracted from video."
            )

        # --- Temporal signals (best-effort, heuristic) ---
        # We keep these lightweight and offline-friendly; this is not a dedicated temporal deepfake model.
        feature_extractor = torch.nn.Sequential(*list(model.children())[:-1]).to(device)
        feature_extractor.eval()

        probs_list: list["torch.Tensor"] = []
        emb_list: list["torch.Tensor"] = []
        labels: list[str] = []
        max_confs: list[float] = []
        entropies: list[float] = []
        l1_diffs: list[float] = []  # normalized L1 distance between consecutive prob vectors (0..1)
        cos_sims: list[float] = []  # cosine similarity between consecutive embeddings (-1..1)
        pixel_diffs: list[float] = []  # mean grayscale diff between consecutive frames (0..1)

        prev_probs: "torch.Tensor | None" = None
        prev_emb: "torch.Tensor | None" = None
        prev_gray_small: "Image.Image | None" = None

        per_frame: list[dict[str, object]] = []
        skipped = 0

        try:
            for fp in frame_paths:
                try:
                    img = Image.open(fp).convert("RGB")
                except Exception:
                    skipped += 1
                    continue
                try:
                    with torch.no_grad():
                        tensor = transform(img).unsqueeze(0).to(device)
                        emb = feature_extractor(tensor).flatten(1)  # (1, D)
                        logits = model.fc(emb)
                        probs = torch.softmax(logits, dim=1).detach().cpu().squeeze(0)
                        emb_cpu = emb.detach().cpu().squeeze(0)
                except Exception:
                    skipped += 1
                    continue
                probs_list.append(probs)
                emb_list.append(emb_cpu)
                best_idx = int(torch.argmax(probs).item())
                best_prob = float(probs[best_idx].item())
                lbl = class_names[best_idx] if best_idx < len(class_names) else str(best_idx)
                labels.append(lbl)
                max_confs.append(best_prob)
                # Entropy of probability distribution (higher = less confident).
                p = probs.clamp(min=1e-12)
                entropies.append(float((-p * torch.log(p)).sum().item()))

                # Temporal diffs vs previous frame.
                if prev_probs is not None:
                    l1 = float(torch.sum(torch.abs(probs - prev_probs)).item())
                    l1_diffs.append(min(max(l1 / 2.0, 0.0), 1.0))
                prev_probs = probs

                if prev_emb is not None:
                    a = emb_cpu
                    b = prev_emb
                    denom = float((a.norm() * b.norm()).item())
                    cos = float((a.dot(b).item() / denom)) if denom > 0 else 0.0
                    cos_sims.append(cos)
                prev_emb = emb_cpu

                gray_small = img.convert("L").resize((64, 64))
                if prev_gray_small is not None:
                    diff = ImageChops.difference(gray_small, prev_gray_small)
                    pixel_diffs.append(float(sum(diff.getdata())) / (64 * 64 * 255))
                prev_gray_small = gray_small

                per_frame.append(
                    {
                        "frame": fp.name,
                        "label": lbl,
                        "confidence": round(best_prob, 6),
                    }
                )

            if not probs_list:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No valid frames could be decoded for inference.",
                )

            mean_probs = torch.stack(probs_list, dim=0).mean(dim=0)
            top_k = max(1, min(int(top_k), int(mean_probs.numel())))
            ranked = sorted(
                list(enumerate(mean_probs.tolist())),
                key=lambda x: x[1],
                reverse=True,
            )[:top_k]
            best_idx, best_prob = ranked[0]

            flip_count = 0
            for a, b in zip(labels, labels[1:]):
                if a != b:
                    flip_count += 1
            flip_rate = float(flip_count / max(1, len(labels) - 1))

            def _stats(values: list[float]) -> dict[str, float]:
                if not values:
                    return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}
                mean = float(statistics.mean(values))
                std = float(statistics.pstdev(values)) if len(values) > 1 else 0.0
                return {
                    "mean": round(mean, 6),
                    "std": round(std, 6),
                    "min": round(float(min(values)), 6),
                    "max": round(float(max(values)), 6),
                }

            temporal = {
                "label_flip_count": int(flip_count),
                "label_flip_rate": round(flip_rate, 6),
                "max_confidence": _stats(max_confs),
                "prob_l1_norm": _stats(l1_diffs),
                "embedding_cosine": _stats(cos_sims),
                "pixel_diff_norm": _stats(pixel_diffs),
                "prob_entropy": _stats(entropies),
                "notes": "Temporal signals (frame deltas, embedding consistency). A learned temporal model may be available via temporal_confidence_model.",
            }

            # Simple heuristic anomaly score in [0, 1].
            emb_penalty = 0.0
            if cos_sims:
                emb_mean = float(statistics.mean(cos_sims))
                emb_penalty = min(max((1.0 - emb_mean) / 0.3, 0.0), 1.0)
            l1_mean = float(statistics.mean(l1_diffs)) if l1_diffs else 0.0
            pix_mean = float(statistics.mean(pixel_diffs)) if pixel_diffs else 0.0
            anomaly = 0.35 * flip_rate + 0.25 * l1_mean + 0.25 * emb_penalty + 0.15 * pix_mean
            temporal["anomaly_score_heuristic"] = round(float(min(max(anomaly, 0.0), 1.0)), 4)

            # --- Temporal deepfake model (trained, not heuristic) ---
            temporal_confidence_model = None
            temporal_label_model = None
            temporal_model_meta: dict[str, object] | None = None
            try:
                from uais_v.models.video_temporal import (
                    build_temporal_feature_dict,
                    predict_temporal_confidence,
                )

                feature_dict = build_temporal_feature_dict(
                    flip_rate=flip_rate,
                    flip_count=flip_count,
                    frames_used=len(probs_list),
                    fps=fps,
                    max_confs=max_confs,
                    l1_diffs=l1_diffs,
                    cos_sims=cos_sims,
                    pixel_diffs=pixel_diffs,
                    entropies=entropies,
                )
                proba, meta = predict_temporal_confidence(feature_dict)
                temporal_model_meta = meta
                temporal["model_features"] = {
                    k: round(float(v), 6) for k, v in feature_dict.items()
                }
                temporal["model"] = meta
                if proba is not None:
                    temporal_confidence_model = round(float(proba), 6)
                    temporal_label_model = "fake" if float(proba) >= 0.5 else "real"
            except Exception as exc:  # pragma: no cover - best effort
                temporal_model_meta = {"available": False, "error": str(exc)}
                temporal["model"] = temporal_model_meta

            return {
                "filename": file.filename,
                "prediction": (
                    class_names[int(best_idx)]
                    if int(best_idx) < len(class_names)
                    else str(best_idx)
                ),
                "label": (
                    class_names[int(best_idx)]
                    if int(best_idx) < len(class_names)
                    else str(best_idx)
                ),
                "confidence": round(float(best_prob), 6),
                "aggregation": "mean_prob",
                "frames_used": len(probs_list),
                "frames_skipped": skipped,
                "fps": fps,
                "temporal_confidence_model": temporal_confidence_model,
                "temporal_label_model": temporal_label_model,
                "temporal": temporal,
                "top_k": [
                    {
                        "label": class_names[int(i)] if int(i) < len(class_names) else str(i),
                        "prob": round(float(p), 6),
                    }
                    for i, p in ranked
                ],
                "per_frame": per_frame[: min(20, len(per_frame))],
                "num_classes": len(class_names),
                "classes": class_names,
            }
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Video predict failed: {exc}",
            ) from exc
