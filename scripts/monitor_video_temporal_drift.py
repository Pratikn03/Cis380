from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
from pathlib import Path
from typing import Iterable

import numpy as np

from app.monitoring.drift import classify_status, psi

VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


def _list_videos(root: Path) -> list[Path]:
    if not root.exists():
        return []
    files: list[Path] = []
    for ext in VIDEO_EXTS:
        files.extend(root.rglob(f"*{ext}"))
        files.extend(root.rglob(f"*{ext.upper()}"))
    return sorted({p for p in files if p.is_file()})


def _dataset_signature(paths: Iterable[Path]) -> dict[str, object]:
    h = hashlib.sha256()
    total_size = 0
    count = 0
    for p in sorted(paths):
        try:
            stat = p.stat()
        except FileNotFoundError:
            continue
        count += 1
        total_size += stat.st_size
        h.update(str(p).encode("utf-8"))
        h.update(str(stat.st_size).encode("utf-8"))
        h.update(str(int(stat.st_mtime)).encode("utf-8"))
    return {"count": count, "total_size": total_size, "signature": h.hexdigest()[:16]}


def _sample_paths(paths: list[Path], max_items: int, seed: int) -> list[Path]:
    if max_items <= 0 or len(paths) <= max_items:
        return paths
    rng = random.Random(seed)
    return rng.sample(paths, k=max_items)


def _load_model(model_path: Path):
    import torch

    from app.models.vision.temporal.model import TemporalDeepfakeLSTM

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = TemporalDeepfakeLSTM(hidden=256, backbone="mobilenet_v3_small", freeze_backbone=True)
    if model_path.exists():
        state = torch.load(model_path, map_location=device)
        model.load_state_dict(state)
    model.to(device)
    model.eval()
    return model, device


def _sample_clip(path: Path, clip_len: int, size: int):
    import cv2
    import torch

    cap = cv2.VideoCapture(str(path))
    frames = []
    while len(frames) < clip_len:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (size, size))
        frame = frame.astype(np.float32) / 255.0
        frames.append(frame)
    cap.release()

    if not frames:
        raise RuntimeError("No valid frames extracted.")
    while len(frames) < clip_len:
        frames.append(frames[-1])
    clip = np.stack(frames[:clip_len])
    return torch.tensor(clip, dtype=torch.float32).permute(0, 3, 1, 2).unsqueeze(0)


def _predict_probs(
    model,
    device: str,
    paths: list[Path],
    *,
    clip_len: int,
    size: int,
) -> tuple[list[float], list[str]]:
    import torch

    probs: list[float] = []
    errors: list[str] = []
    for p in paths:
        try:
            clip = _sample_clip(p, clip_len=clip_len, size=size).to(device)
            with torch.no_grad():
                logits = model(clip)
                prob = torch.sigmoid(logits).item()
            probs.append(float(prob))
        except Exception as exc:
            errors.append(f"{p.name}: {exc}")
    return probs, errors


def _stats(values: list[float]) -> dict[str, float]:
    if not values:
        return {"n": 0, "mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}
    arr = np.asarray(values, dtype=float)
    return {
        "n": int(arr.size),
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
    }


def _psi_score(baseline: list[float], current: list[float]) -> float:
    if not baseline or not current:
        return 0.0
    return float(psi(baseline, current, bins=10))


def main() -> int:
    ap = argparse.ArgumentParser(description="Monitor LSTM drift for video temporal model.")
    ap.add_argument("--root", default="data/raw/vision/video")
    ap.add_argument("--real-dir", default=None)
    ap.add_argument("--fake-dir", default=None)
    ap.add_argument(
        "--model-path",
        default=os.getenv("TEMPORAL_MODEL_PATH", "artifacts/vision_temporal/temporal_lstm.pt"),
    )
    ap.add_argument("--baseline", default="reports/vision_temporal_lstm_baseline.json")
    ap.add_argument("--report", default="reports/vision_temporal_lstm_drift.json")
    ap.add_argument("--max-per-class", type=int, default=60)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--clip-len", type=int, default=int(os.getenv("HLS_CLIP_LEN", "16")))
    ap.add_argument("--frame-size", type=int, default=int(os.getenv("HLS_FRAME_SIZE", "224")))
    ap.add_argument("--update-baseline", action="store_true")
    args = ap.parse_args()

    root = Path(args.root)
    real_dir = Path(args.real_dir) if args.real_dir else root / "real"
    fake_dir = Path(args.fake_dir) if args.fake_dir else root / "fake"
    baseline_path = Path(args.baseline)
    report_path = Path(args.report)
    model_path = Path(args.model_path)

    real_paths = _list_videos(real_dir)
    fake_paths = _list_videos(fake_dir)
    if not real_paths or not fake_paths:
        raise SystemExit(
            f"No videos found. real={len(real_paths)} fake={len(fake_paths)} under {root}"
        )

    real_sample = _sample_paths(real_paths, args.max_per_class, args.seed)
    fake_sample = _sample_paths(fake_paths, args.max_per_class, args.seed + 1)

    model, device = _load_model(model_path)
    real_probs, real_errors = _predict_probs(
        model, device, real_sample, clip_len=args.clip_len, size=args.frame_size
    )
    fake_probs, fake_errors = _predict_probs(
        model, device, fake_sample, clip_len=args.clip_len, size=args.frame_size
    )
    all_probs = real_probs + fake_probs
    errors = real_errors + fake_errors

    dataset_sig = {
        "real": _dataset_signature(real_paths),
        "fake": _dataset_signature(fake_paths),
    }

    baseline = None
    if baseline_path.exists():
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

    if baseline is None or args.update_baseline:
        baseline = {
            "generated_at": str(np.datetime64("now")),
            "dataset": dataset_sig,
            "model_path": str(model_path),
            "clip_len": int(args.clip_len),
            "frame_size": int(args.frame_size),
            "probs": {"all": all_probs, "real": real_probs, "fake": fake_probs},
            "stats": {
                "all": _stats(all_probs),
                "real": _stats(real_probs),
                "fake": _stats(fake_probs),
            },
        }
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text(json.dumps(baseline, indent=2), encoding="utf-8")

    base_probs = baseline.get("probs", {})
    psi_all = _psi_score(base_probs.get("all", []), all_probs)
    psi_real = _psi_score(base_probs.get("real", []), real_probs)
    psi_fake = _psi_score(base_probs.get("fake", []), fake_probs)
    drift_score = float(np.mean([psi_all, psi_real, psi_fake]))
    status = classify_status(drift_score)

    reasons = []
    if baseline.get("dataset") != dataset_sig:
        reasons.append("dataset_signature_changed")
    if status != "ok":
        reasons.append(f"drift_status_{status}")

    report = {
        "generated_at": str(np.datetime64("now")),
        "baseline_path": str(baseline_path),
        "model_path": str(model_path),
        "clip_len": int(args.clip_len),
        "frame_size": int(args.frame_size),
        "dataset": dataset_sig,
        "stats": {
            "all": _stats(all_probs),
            "real": _stats(real_probs),
            "fake": _stats(fake_probs),
        },
        "psi": {"all": psi_all, "real": psi_real, "fake": psi_fake, "mean": drift_score},
        "status": status,
        "retrain_recommended": bool(reasons),
        "retrain_reasons": reasons,
        "errors": errors[:10],
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[video-temporal-drift] wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
