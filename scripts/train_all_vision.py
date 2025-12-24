#!/usr/bin/env python3
"""One-command vision training orchestration.

This repo accumulated multiple one-off vision training scripts. The canonical
entrypoints are now:

- `scripts/train_all_vision_full.py` (deepfake + real/fake image classifiers)
- `scripts/prepare_brand_data.py` + `python -m src.train.train_brand_logo_detector` (brand/logo YOLO)
- `src/train/train_video_temporal.py` (video temporal classifier)

Keep this file as a stable wrapper so older docs/bookmarks still work:
  python scripts/train_all_vision.py
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"


def _run(cmd: list[str]) -> None:
    """Run a subprocess from repo root and raise on failure."""
    print("\n$", " ".join(cmd))
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    subprocess.run(cmd, cwd=str(REPO_ROOT), check=True, env=env)


def main() -> int:
    parser = argparse.ArgumentParser(description="Train all vision models (brand + deepfake + real/fake + video).")

    parser.add_argument("--skip-full", action="store_true", help="Skip deepfake + real/fake image training.")
    parser.add_argument("--skip-brand", action="store_true", help="Skip brand/logo detector training (YOLO).")
    parser.add_argument("--skip-temporal", action="store_true", help="Skip video temporal model training.")

    # Forwarded to scripts/train_all_vision_full.py when enabled.
    parser.add_argument("--device", default="auto", help="auto|cpu|cuda|mps (forwarded to full training).")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (forwarded to full training).")
    parser.add_argument("--epochs", type=int, default=3, help="Epochs per model (forwarded to full training).")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size (forwarded to full training).")
    parser.add_argument("--num-workers", type=int, default=0, help="DataLoader workers (forwarded to full training).")
    parser.add_argument("--val-split", type=float, default=0.15, help="Val split for real/fake (forwarded).")
    parser.add_argument("--max-train", type=int, default=0, help="Cap training samples (0 = no cap).")
    parser.add_argument("--max-val", type=int, default=0, help="Cap validation samples (0 = no cap).")
    parser.add_argument("--no-pretrained", action="store_true", help="Disable ImageNet pretrained weights.")
    parser.add_argument("--out-dir", default=str(REPO_ROOT / "models" / "vision"), help="Output dir for vision weights.")
    parser.add_argument("--celeb-root", default=str(REPO_ROOT / "data" / "Celeb_V2"), help="Celeb_V2 dataset root.")
    parser.add_argument(
        "--raw-vision-root",
        default=str(REPO_ROOT / "data" / "raw" / "vision"),
        help="Raw vision dataset root (train_real/train_fake).",
    )

    args = parser.parse_args()

    if not args.skip_full:
        _run(
            [
                sys.executable,
                "scripts/train_all_vision_full.py",
                "--device",
                str(args.device),
                "--seed",
                str(int(args.seed)),
                "--epochs",
                str(int(args.epochs)),
                "--batch-size",
                str(int(args.batch_size)),
                "--num-workers",
                str(int(args.num_workers)),
                "--val-split",
                str(float(args.val_split)),
                "--max-train",
                str(int(args.max_train)),
                "--max-val",
                str(int(args.max_val)),
                "--out-dir",
                str(args.out_dir),
                "--celeb-root",
                str(args.celeb_root),
                "--raw-vision-root",
                str(args.raw_vision_root),
            ]
            + (["--no-pretrained"] if args.no_pretrained else [])
        )

    if not args.skip_brand:
        _run([sys.executable, "scripts/prepare_brand_data.py"])
        _run([sys.executable, "-m", "src.train.train_brand_logo_detector"])

    if not args.skip_temporal:
        _run([sys.executable, "src/train/train_video_temporal.py"])

    print("\n✅ Vision training complete.")
    print("   - Deepfake/RealFake weights: models/vision/*.pt")
    print("   - Brand YOLO weights: artifacts/brand/yolo_logo_det.pt")
    print("   - Video temporal model: models/vision/video_temporal_model.pkl")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
