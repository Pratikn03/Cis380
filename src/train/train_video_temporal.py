"""Train a lightweight temporal deepfake model for video inference.

This learns a classifier from per-video temporal-consistency features derived from
sampled frames (probs deltas, embedding cosine similarity, pixel diffs, entropy).

Output artifact:
  models/vision/video_temporal_model.pkl
"""

from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import subprocess
import tempfile
from pathlib import Path
import numpy as np
import joblib

from uais_v.models.video_temporal import (
    LABEL_MAP,
    TEMPORAL_FEATURE_NAMES,
    VIDEO_TEMPORAL_MODEL_PATH,
    build_temporal_feature_dict,
    vectorize_temporal_features,
)

VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


def _resolve_device(requested: str | None) -> str:
    req = (requested or "").strip()
    if req and req.lower() != "auto":
        return req
    try:  # pragma: no cover - hardware-dependent
        import torch

        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"


def _load_class_names() -> list[str]:
    path = Path("models/vision/resnet/classes.txt")
    if path.exists():
        names = [
            line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
        ]
        if names:
            return names
    return ["fake", "real"]


def _load_vision_predictor(*, device: str = "cpu"):
    import torch
    from torchvision import transforms

    from uais_v.models.vision_resnet import VisionConfig as ResNetCfg, build_resnet_classifier

    model_path = Path("models/vision/resnet/model.pt")
    if not model_path.exists():
        raise FileNotFoundError(f"Missing {model_path}. Train the vision model first.")

    class_names = _load_class_names()
    model = build_resnet_classifier(ResNetCfg(num_classes=len(class_names), pretrained=False)).to(
        torch.device(device)
    )
    state = torch.load(model_path, map_location=torch.device(device))
    model.load_state_dict(state, strict=True)
    model.eval()

    transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    feature_extractor = torch.nn.Sequential(*list(model.children())[:-1]).to(torch.device(device))
    feature_extractor.eval()
    return model, feature_extractor, transform, class_names, torch.device(device)


def _extract_frames(*, video_path: Path, fps: float, max_frames: int, ffmpeg: str) -> list[Path]:
    frames_dir = Path(tempfile.mkdtemp(prefix="Sentifargo_video_frames_"))
    # PNG avoids ffmpeg's MJPEG full-range YUV edge cases on some downloaded videos.
    out_pattern = frames_dir / "frame_%06d.png"

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

    subprocess.run(cmd, check=True)
    return sorted(frames_dir.glob("frame_*.png"))


def _compute_features_for_video(
    *,
    video_path: Path,
    label: int,
    model,
    feature_extractor,
    transform,
    class_names: list[str],
    device,
    fps: float,
    max_frames: int,
    ffmpeg: str,
) -> tuple[np.ndarray, int]:
    from PIL import Image, ImageChops
    import torch

    frames_dir: Path | None = None
    try:
        frame_paths = _extract_frames(
            video_path=video_path, fps=fps, max_frames=max_frames, ffmpeg=ffmpeg
        )
        if not frame_paths:
            raise RuntimeError("no frames extracted")
        frames_dir = frame_paths[0].parent

        max_confs: list[float] = []
        entropies: list[float] = []
        l1_diffs: list[float] = []
        cos_sims: list[float] = []
        pixel_diffs: list[float] = []
        labels: list[str] = []

        prev_probs: "torch.Tensor | None" = None
        prev_emb: "torch.Tensor | None" = None
        prev_gray_small: "Image.Image | None" = None

        used = 0
        with torch.no_grad():
            for fp in frame_paths:
                img = Image.open(fp).convert("RGB")
                tensor = transform(img).unsqueeze(0).to(device)
                emb = feature_extractor(tensor).flatten(1)  # (1, D)
                logits = model.fc(emb)
                probs = torch.softmax(logits, dim=1).detach().cpu().squeeze(0)
                emb_cpu = emb.detach().cpu().squeeze(0)

                best_idx = int(torch.argmax(probs).item())
                best_prob = float(probs[best_idx].item())
                lbl = class_names[best_idx] if best_idx < len(class_names) else str(best_idx)
                labels.append(lbl)
                max_confs.append(best_prob)

                p = probs.clamp(min=1e-12)
                entropies.append(float((-p * torch.log(p)).sum().item()))

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
                used += 1

        flip_count = sum(1 for a, b in zip(labels, labels[1:]) if a != b)
        flip_rate = float(flip_count / max(1, len(labels) - 1))

        feature_dict = build_temporal_feature_dict(
            flip_rate=flip_rate,
            flip_count=flip_count,
            frames_used=used,
            fps=fps,
            max_confs=max_confs,
            l1_diffs=l1_diffs,
            cos_sims=cos_sims,
            pixel_diffs=pixel_diffs,
            entropies=entropies,
        )
        X = vectorize_temporal_features(feature_dict, feature_names=TEMPORAL_FEATURE_NAMES)
        return X, int(label)
    finally:
        if frames_dir is not None and frames_dir.exists():
            shutil.rmtree(frames_dir, ignore_errors=True)


def _list_videos(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    files: list[Path] = []
    for ext in VIDEO_EXTS:
        files.extend(folder.glob(f"*{ext}"))
        files.extend(folder.glob(f"*{ext.upper()}"))
    return sorted({p for p in files if p.is_file()})


def _best_binary_threshold(
    y_true: np.ndarray,
    proba: np.ndarray,
) -> tuple[float, dict[str, float]]:
    from sklearn.metrics import accuracy_score, f1_score

    candidates = np.unique(np.clip(proba, 0.0, 1.0))
    if candidates.size == 0:
        candidates = np.asarray([0.5], dtype=float)
    candidates = np.unique(np.concatenate([candidates, np.asarray([0.5], dtype=float)]))
    best_threshold = 0.5
    best_metrics = {"accuracy": -1.0, "f1": -1.0}
    for threshold in candidates:
        pred = (proba >= float(threshold)).astype(int)
        acc = float(accuracy_score(y_true, pred))
        f1 = float(f1_score(y_true, pred, zero_division=0))
        if (acc, f1) > (best_metrics["accuracy"], best_metrics["f1"]):
            best_threshold = float(threshold)
            best_metrics = {"accuracy": acc, "f1": f1}
    return best_threshold, best_metrics


def main() -> int:
    parser = argparse.ArgumentParser(description="Train a video temporal deepfake model (sklearn).")
    parser.add_argument("--real-dir", type=Path, default=Path("data/raw/vision/video/real"))
    parser.add_argument("--fake-dir", type=Path, default=Path("data/raw/vision/video/fake"))
    parser.add_argument("--fps", type=float, default=1.0)
    parser.add_argument("--max-frames", type=int, default=0)
    parser.add_argument(
        "--max-per-class",
        type=int,
        default=0,
        help="Maximum videos per class; 0 uses the full available dataset.",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--device",
        type=str,
        default=os.getenv("Sentifargo_VISION_DEVICE", "auto"),
    )
    parser.add_argument("--out", type=Path, default=VIDEO_TEMPORAL_MODEL_PATH)
    args = parser.parse_args()

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg not found on PATH. Install it (macOS: brew install ffmpeg).")

    real_videos = _list_videos(args.real_dir)
    fake_videos = _list_videos(args.fake_dir)
    if not real_videos or not fake_videos:
        raise SystemExit(f"Missing videos. Found real={len(real_videos)} fake={len(fake_videos)}")

    rng = random.Random(int(args.seed))
    rng.shuffle(real_videos)
    rng.shuffle(fake_videos)

    max_per = int(args.max_per_class)
    if max_per > 0:
        real_videos = real_videos[:max_per]
        fake_videos = fake_videos[:max_per]
    print(
        f"[video-temporal] Using real={len(real_videos)} fake={len(fake_videos)} videos",
        flush=True,
    )

    device_name = _resolve_device(str(args.device))
    print(f"[video-temporal] device={device_name}", flush=True)
    model, feature_extractor, transform, class_names, device = _load_vision_predictor(
        device=device_name
    )

    X_rows: list[np.ndarray] = []
    y_rows: list[int] = []
    failures: list[str] = []

    processed = 0
    total_videos = len(real_videos) + len(fake_videos)
    for label_name, videos in [("real", real_videos), ("fake", fake_videos)]:
        label = int(LABEL_MAP[label_name])
        for vp in videos:
            try:
                X, y = _compute_features_for_video(
                    video_path=vp,
                    label=label,
                    model=model,
                    feature_extractor=feature_extractor,
                    transform=transform,
                    class_names=class_names,
                    device=device,
                    fps=float(args.fps),
                    max_frames=int(args.max_frames),
                    ffmpeg=str(ffmpeg),
                )
                X_rows.append(X)
                y_rows.append(y)
            except Exception as exc:
                failures.append(f"{vp.name}: {exc}")
            finally:
                processed += 1
                if processed == 1 or processed % 25 == 0 or processed == total_videos:
                    print(
                        "[video-temporal] processed "
                        f"{processed}/{total_videos} videos "
                        f"(features={len(X_rows)} failures={len(failures)})",
                        flush=True,
                    )

    if not X_rows:
        raise SystemExit("No training samples could be processed (all videos failed).")

    X_all = np.concatenate(X_rows, axis=0)
    y_all = np.asarray(y_rows, dtype=int)

    from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
    from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.svm import SVC

    X_train_full, X_test, y_train_full, y_test = train_test_split(
        X_all,
        y_all,
        test_size=0.25,
        random_state=int(args.seed),
        stratify=y_all if len(set(y_all.tolist())) > 1 else None,
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_full,
        y_train_full,
        test_size=0.25,
        random_state=int(args.seed) + 1,
        stratify=y_train_full if len(set(y_train_full.tolist())) > 1 else None,
    )

    candidates = {
        "logreg": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("model", LogisticRegression(max_iter=1000, class_weight="balanced")),
            ]
        ),
        "svc_rbf": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("model", SVC(C=2.0, gamma="scale", probability=True, class_weight="balanced")),
            ]
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=400,
            max_depth=8,
            min_samples_leaf=3,
            class_weight="balanced_subsample",
            random_state=int(args.seed),
            n_jobs=-1,
        ),
        "extra_trees": ExtraTreesClassifier(
            n_estimators=500,
            max_depth=None,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=int(args.seed),
            n_jobs=-1,
        ),
        "hist_gb": HistGradientBoostingClassifier(
            max_iter=250,
            learning_rate=0.04,
            max_leaf_nodes=15,
            l2_regularization=0.05,
            random_state=int(args.seed),
        ),
    }

    best: dict[str, object] | None = None
    candidate_results: list[dict[str, float | str]] = []
    for name, candidate in candidates.items():
        candidate.fit(X_train, y_train)
        val_proba = candidate.predict_proba(X_val)[:, 1]
        threshold, val_selected = _best_binary_threshold(y_val, val_proba)
        val_pred = (val_proba >= threshold).astype(int)
        val_roc = (
            float(roc_auc_score(y_val, val_proba))
            if len(set(y_val.tolist())) > 1
            else float("nan")
        )
        result = {
            "name": name,
            "threshold": float(threshold),
            "val_accuracy": float(accuracy_score(y_val, val_pred)),
            "val_f1": float(f1_score(y_val, val_pred, zero_division=0)),
            "val_roc_auc": val_roc,
        }
        candidate_results.append(result)
        key = (result["val_accuracy"], result["val_f1"], result["val_roc_auc"])
        if best is None or key > best["key"]:  # type: ignore[operator]
            best = {
                "name": name,
                "model": candidate,
                "threshold": threshold,
                "key": key,
                "val": val_selected,
            }

    if best is None:
        raise SystemExit("No temporal classifier candidate could be trained.")

    clf = best["model"]
    threshold = float(best["threshold"])
    proba = clf.predict_proba(X_test)[:, 1]  # type: ignore[union-attr]
    pred = (proba >= threshold).astype(int)
    metrics = {
        "accuracy": float(accuracy_score(y_test, pred)),
        "f1": float(f1_score(y_test, pred, zero_division=0)),
        "roc_auc": (
            float(roc_auc_score(y_test, proba)) if len(set(y_test.tolist())) > 1 else float("nan")
        ),
        "threshold": threshold,
        "selected_model": str(best["name"]),
        "candidate_results": candidate_results,
        "n_train": int(len(y_train)),
        "n_val": int(len(y_val)),
        "n_test": int(len(y_test)),
        "n_total": int(len(y_all)),
        "failures": int(len(failures)),
        "fps": float(args.fps),
        "max_frames": int(args.max_frames),
        "feature_names": list(TEMPORAL_FEATURE_NAMES),
    }
    print("[video-temporal] metrics:", metrics)
    if failures:
        print("[video-temporal] sample failures:", failures[:5])

    args.out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": clf,
            "scaler": None,
            "feature_names": list(TEMPORAL_FEATURE_NAMES),
            "label_map": dict(LABEL_MAP),
            "threshold": threshold,
            "metrics": metrics,
        },
        args.out,
    )
    print(f"[video-temporal] saved: {args.out}")

    out_metrics = Path("experiments/vision/video_temporal/metrics.json")
    out_metrics.parent.mkdir(parents=True, exist_ok=True)
    out_metrics.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"[video-temporal] wrote: {out_metrics}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
