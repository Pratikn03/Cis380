"""One-command trainer for UAIS/OmniChatX artifacts.

This script re-runs the core experiment pipelines and refreshes the artifacts
under `models/` and `experiments/`.

It is intentionally conservative:
- Runs fraud/cyber/behavior/fusion (fast-ish, pure sklearn).
- Retrains voice emotion model (sampled) to keep artifact compatible.
- Runs the recommender meta-action trainer.
- Vision training is optional (can be heavy) and is OFF by default.

Usage:
  python scripts/train_all.py
  python scripts/train_all.py --with-vision
  python scripts/train_all.py --with-video-temporal
  python scripts/train_all.py --voice-limit-per-class 500
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run(args: list[str]) -> None:
    """Run a subprocess from repo root and raise on failure."""
    print("\n$", " ".join(args))
    env = os.environ.copy()
    # Ensure `import uais` works when executing files directly.
    src_dir = str(REPO_ROOT / "src")
    env["PYTHONPATH"] = src_dir + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    subprocess.run(args, cwd=str(REPO_ROOT), check=True, env=env)


def main() -> int:
    parser = argparse.ArgumentParser(description="Train all core UAIS/OmniChatX models")
    parser.add_argument(
        "--with-vision",
        action="store_true",
        help="Also run vision training (may be slow / require GPU / dataset layout).",
    )
    parser.add_argument(
        "--with-video-temporal",
        action="store_true",
        help="Also train the video temporal deepfake model (requires data/raw/vision/video/{real,fake} + ffmpeg).",
    )
    parser.add_argument(
        "--voice-limit-per-class",
        type=int,
        default=200,
        help="Max WAVs per class to use for voice training (0 uses all).",
    )
    args = parser.parse_args()

    # Core tabular domains
    _run([sys.executable, "src/scripts/run_fraud_experiment.py"])
    _run([sys.executable, "src/scripts/run_cyber_experiment.py"])
    _run([sys.executable, "src/scripts/run_behavior_experiment.py"])
    _run([sys.executable, "src/scripts/run_fusion_experiment.py"])

    # Voice
    _run(
        [
            sys.executable,
            "app/models/voice/emotion_train.py",
            "--limit-per-class",
            str(int(args.voice_limit_per_class)),
        ]
    )

    # Recommender
    _run([sys.executable, "src/train/train_recommender.py"])

    # Vision is optional/heavy.
    if args.with_vision:
        # UAIS-V vision training entrypoints can vary by dataset. If you have
        # a dedicated script, wire it here.
        candidate = REPO_ROOT / "scripts" / "run_train_vision.sh"
        if candidate.exists():
            _run(["bash", str(candidate)])
        else:
            print("\n[train_all] --with-vision requested, but scripts/run_train_vision.sh not found; skipping.")

    if args.with_video_temporal:
        # Trains a lightweight sklearn temporal model used by /api/vision/video/predict.
        _run([sys.executable, "src/train/train_video_temporal.py"])

    print("\n✅ Training complete. Check experiments/*/metrics and models/* outputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
