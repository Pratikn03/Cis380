from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any


class FaceEmotionModelNotTrainedError(RuntimeError):
    pass


MODEL_PATH = Path("models/vision/face_emotion/model.pt")
CLASSES_PATH = Path("models/vision/face_emotion/classes.txt")


def _resolve_device(requested: str) -> str:
    req = (requested or "").strip()
    if not req or req.lower() == "auto":
        try:  # pragma: no cover - depends on local hardware
            import torch

            if torch.backends.mps.is_available():
                return "mps"
            if torch.cuda.is_available():
                return "cuda"
        except Exception:
            pass
        return "cpu"
    return req


def _build_model(arch: str, *, num_classes: int, pretrained: bool):
    from torch import nn
    from torchvision import models

    a = (arch or "small_cnn").strip().lower()
    if a == "resnet18":
        weights = models.ResNet18_Weights.DEFAULT if pretrained else None
        model = models.resnet18(weights=weights)
        in_feat = int(model.fc.in_features)
        model.fc = nn.Linear(in_feat, num_classes)
        return model
    if a != "small_cnn":
        raise ValueError("arch must be one of: small_cnn, resnet18")

    class SmallCNN(nn.Module):
        def __init__(self, classes: int):
            super().__init__()
            self.features = nn.Sequential(
                nn.Conv2d(3, 32, 3, padding=1),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(2),
                nn.Conv2d(32, 64, 3, padding=1),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(2),
                nn.Conv2d(64, 128, 3, padding=1),
                nn.ReLU(inplace=True),
                nn.AdaptiveAvgPool2d((1, 1)),
            )
            self.classifier = nn.Linear(128, classes)

        def forward(self, x):
            x = self.features(x)
            x = x.flatten(1)
            return self.classifier(x)

    return SmallCNN(num_classes)


def _load_classes_fallback() -> list[str]:
    if CLASSES_PATH.exists():
        try:
            classes = [line.strip() for line in CLASSES_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
            if classes:
                return classes
        except Exception:
            pass
    return ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]


@lru_cache(maxsize=1)
def _load_face_emotion_predictor():
    """Load the face emotion model + transform (cached)."""
    try:
        import torch
        from torchvision import transforms
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(f"torch/torchvision not available: {exc}") from exc

    if not MODEL_PATH.exists():
        raise FaceEmotionModelNotTrainedError(
            f"Face emotion model not found at {MODEL_PATH}. "
            "Train it with: python -m src.train.train_face_emotion --data-dir <your_dataset>"
        )

    device_env = (os.getenv("Sentifargo_FACE_EMOTION_DEVICE") or "").strip()
    device = torch.device(_resolve_device(device_env) if device_env else "cpu")

    ckpt = torch.load(MODEL_PATH, map_location="cpu")
    if isinstance(ckpt, dict) and "state_dict" in ckpt:
        arch = str(ckpt.get("arch") or "small_cnn")
        pretrained = bool(ckpt.get("pretrained") or False)
        image_size = int(ckpt.get("image_size") or 96)
        classes = list(ckpt.get("classes") or _load_classes_fallback())
        mean = list(ckpt.get("mean") or [0.485, 0.456, 0.406])
        std = list(ckpt.get("std") or [0.229, 0.224, 0.225])
        state = ckpt["state_dict"]
    else:
        # Backward-compatible: support plain state_dict checkpoints.
        arch = "small_cnn"
        pretrained = False
        image_size = 96
        classes = _load_classes_fallback()
        mean = [0.485, 0.456, 0.406]
        std = [0.229, 0.224, 0.225]
        state = ckpt

    model = _build_model(arch, num_classes=len(classes), pretrained=pretrained)
    model.load_state_dict(state, strict=True)
    model.to(device)
    model.eval()

    def _to_rgb(im):
        return im.convert("RGB")

    transform = transforms.Compose(
        [
            transforms.Resize((int(image_size), int(image_size))),
            transforms.Lambda(_to_rgb),
            transforms.ToTensor(),
            transforms.Normalize(mean=mean, std=std),
        ]
    )

    return model, transform, classes, device, {"arch": arch, "image_size": image_size}


def predict_face_emotion(*, image_bytes: bytes, filename: str | None = None, top_k: int = 3) -> dict[str, Any]:
    """Predict face emotion from an image (expects a face crop or selfie-style photo)."""
    try:
        import io

        import torch
        from PIL import Image
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"Missing deps: {exc}") from exc

    model, transform, classes, device, meta = _load_face_emotion_predictor()

    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as exc:
        raise ValueError(f"Invalid image: {exc}") from exc

    tensor = transform(image).unsqueeze(0).to(device)
    with torch.no_grad():
        logits = model(tensor)
        probs = torch.softmax(logits, dim=1).detach().cpu().numpy().ravel().tolist()

    if not probs:
        raise RuntimeError("Empty prediction output.")

    top_k = max(1, min(int(top_k), len(probs)))
    ranked = sorted(enumerate(probs), key=lambda x: x[1], reverse=True)[:top_k]
    best_idx, best_prob = ranked[0]

    return {
        "filename": filename,
        "emotion": classes[int(best_idx)] if int(best_idx) < len(classes) else str(best_idx),
        "confidence": round(float(best_prob), 6),
        "top_k": [
            {
                "emotion": classes[int(i)] if int(i) < len(classes) else str(i),
                "prob": round(float(p), 6),
            }
            for i, p in ranked
        ],
        "num_classes": len(classes),
        "classes": classes,
        "model_path": str(MODEL_PATH),
        "model_meta": meta,
    }

