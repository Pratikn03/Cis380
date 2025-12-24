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

import joblib
import numpy as np

from uais_v.models.video_temporal import (
    LABEL_MAP,
    TEMPORAL_FEATURE_NAMES,
    VIDEO_TEMPORAL_MODEL_PATH,
    build_temporal_feature_dict,
    vectorize_temporal_features,
)


VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


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
    frames_dir = Path(tempfile.mkdtemp(prefix="omnichatx_video_frames_"))
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

    subprocess.run(cmd, check=True)
    return sorted(frames_dir.glob("frame_*.jpg"))


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Train a video temporal deepfake model (sklearn).")
    parser.add_argument("--real-dir", type=Path, default=Path("data/raw/vision/video/real"))
    parser.add_argument("--fake-dir", type=Path, default=Path("data/raw/vision/video/fake"))
    parser.add_argument("--fps", type=float, default=1.0)
    parser.add_argument("--max-frames", type=int, default=30)
    parser.add_argument("--max-per-class", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", type=str, default=os.getenv("UAIS_VISION_DEVICE", "cpu"))
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

    max_per = max(1, int(args.max_per_class))
    real_videos = real_videos[:max_per]
    fake_videos = fake_videos[:max_per]
    print(f"[video-temporal] Using real={len(real_videos)} fake={len(fake_videos)} videos")

    model, feature_extractor, transform, class_names, device = _load_vision_predictor(
        device=str(args.device)
    )

    X_rows: list[np.ndarray] = []
    y_rows: list[int] = []
    failures: list[str] = []

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

    if not X_rows:
        raise SystemExit("No training samples could be processed (all videos failed).")

    X_all = np.concatenate(X_rows, axis=0)
    y_all = np.asarray(y_rows, dtype=int)

    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    X_train, X_test, y_train, y_test = train_test_split(
        X_all,
        y_all,
        test_size=0.25,
        random_state=int(args.seed),
        stratify=y_all if len(set(y_all.tolist())) > 1 else None,
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    clf = LogisticRegression(max_iter=300, class_weight="balanced")
    clf.fit(X_train_s, y_train)

    proba = clf.predict_proba(X_test_s)[:, 1]
    pred = (proba >= 0.5).astype(int)
    metrics = {
        "accuracy": float(accuracy_score(y_test, pred)),
        "f1": float(f1_score(y_test, pred, zero_division=0)),
        "roc_auc": (
            float(roc_auc_score(y_test, proba)) if len(set(y_test.tolist())) > 1 else float("nan")
        ),
        "n_train": int(len(y_train)),
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
            "scaler": scaler,
            "feature_names": list(TEMPORAL_FEATURE_NAMES),
            "label_map": dict(LABEL_MAP),
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
