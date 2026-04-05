"""One-command trainer for Sentifargo artifacts.

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


def _run(args: list[str], env_override: dict[str, str] | None = None) -> None:
    """Run a subprocess from repo root and raise on failure."""
    print("\n$", " ".join(args))
    env = os.environ.copy()
    # Ensure `import uais` works when executing files directly.
    src_dir = str(REPO_ROOT / "src")
    env["PYTHONPATH"] = src_dir + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    if env_override:
        env.update(env_override)
    subprocess.run(args, cwd=str(REPO_ROOT), check=True, env=env)


def main() -> int:
    parser = argparse.ArgumentParser(description="Train all core Sentifargo models")
    parser.add_argument(
        "--with-vision",
        action="store_true",
        help="Also run vision training (may be slow / require GPU / dataset layout).",
    )
    parser.add_argument(
        "--with-vision-full",
        action="store_true",
        help="Train full deepfake + real/fake vision models (requires local datasets; can be very slow).",
    )
    parser.add_argument(
        "--vision-full-device",
        type=str,
        default=os.getenv("Sentifargo_VISION_FULL_DEVICE", "cpu"),
        help="Device for train_all_vision_full.py (auto|cpu|cuda|mps). Default: cpu.",
    )
    parser.add_argument(
        "--vision-full-pretrained",
        action="store_true",
        help="Use pretrained weights for vision full (may download from internet).",
    )
    parser.add_argument(
        "--vision-full-epochs",
        type=int,
        default=0,
        help="Override vision full epochs (0 uses script default).",
    )
    parser.add_argument(
        "--vision-full-batch-size",
        type=int,
        default=0,
        help="Override vision full batch size (0 uses script default).",
    )
    parser.add_argument(
        "--vision-full-max-train",
        type=int,
        default=0,
        help="Cap vision full training samples (0 = no cap).",
    )
    parser.add_argument(
        "--vision-full-max-val",
        type=int,
        default=0,
        help="Cap vision full validation samples (0 = no cap).",
    )
    parser.add_argument(
        "--with-brand",
        action="store_true",
        help="Also train the brand/logo detector (requires ultralytics + data/raw/brand).",
    )
    parser.add_argument(
        "--with-video-temporal",
        action="store_true",
        help="Also train the video temporal deepfake model (requires data/raw/vision/video/{real,fake} + ffmpeg).",
    )
    parser.add_argument(
        "--with-face-emotion",
        action="store_true",
        help="Also train the 7-class face emotion model (requires data/raw/vision/face_emotion).",
    )
    parser.add_argument(
        "--face-emotion-data-dir",
        default=str(REPO_ROOT / "data" / "raw" / "vision" / "face_emotion"),
        help="Dataset root for face emotion training (ImageFolder-style).",
    )
    parser.add_argument(
        "--voice-limit-per-class",
        type=int,
        default=200,
        help="Max WAVs per class to use for voice training (0 uses all).",
    )
    parser.add_argument(
        "--fraud-plots",
        action="store_true",
        help="Enable fraud PR/ROC plots (disabled by default for stability).",
    )
    parser.add_argument(
        "--with-stt",
        action="store_true",
        help="Run STT data bootstrap + manifest/splits + evaluation (offline).",
    )
    parser.add_argument(
        "--stt-bootstrap-limit",
        type=int,
        default=200,
        help="Max audio files for STT bootstrap (0 uses all).",
    )
    parser.add_argument(
        "--stt-language",
        type=str,
        default="en",
        help="Language code for STT bootstrap/eval.",
    )
    parser.add_argument(
        "--stt-model-size",
        type=str,
        default="",
        help="Override Whisper model size for STT (sets WHISPER_MODEL).",
    )
    parser.add_argument(
        "--with-stt-train",
        action="store_true",
        help="Also fine-tune Whisper using manifest train/val CSVs.",
    )
    args = parser.parse_args()

    # Core tabular domains
    _run(
        [sys.executable, "src/scripts/run_fraud_experiment.py"],
        env_override={"Sentifargo_FRAUD_SKIP_PLOTS": "false" if args.fraud_plots else "true"},
    )
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

    if args.with_stt:
        env = {"WHISPER_MODEL": args.stt_model_size} if args.stt_model_size else None
        stt_bootstrap = [
            sys.executable,
            "scripts/stt/bootstrap_transcripts.py",
            "--audio-root",
            str(REPO_ROOT / "data" / "raw" / "voice" / "AudioWAV"),
            "--out",
            str(REPO_ROOT / "data" / "raw" / "stt" / "transcripts.jsonl"),
            "--language",
            args.stt_language,
            "--limit",
            str(args.stt_bootstrap_limit),
        ]
        _run(stt_bootstrap, env_override=env)
        _run(
            [
                sys.executable,
                "scripts/stt/build_manifest.py",
                "--transcripts",
                str(REPO_ROOT / "data" / "raw" / "stt" / "transcripts.jsonl"),
                "--out",
                str(REPO_ROOT / "data" / "raw" / "stt" / "manifest.csv"),
                "--normalize",
                "--require-text",
            ]
        )
        _run(
            [
                sys.executable,
                "scripts/stt/split_manifest.py",
                "--manifest",
                str(REPO_ROOT / "data" / "raw" / "stt" / "manifest.csv"),
                "--group-by",
                "speaker_id",
            ]
        )
        _run(
            [
                sys.executable,
                "scripts/stt/validate_manifest.py",
                "--manifest",
                str(REPO_ROOT / "data" / "raw" / "stt" / "manifest.with_splits.csv"),
            ]
        )
        _run(
            [
                sys.executable,
                "scripts/stt/evaluate_stt.py",
                "--manifest",
                str(REPO_ROOT / "data" / "raw" / "stt" / "manifest.with_splits.csv"),
                "--split",
                "test",
                "--limit",
                str(min(100, args.stt_bootstrap_limit) if args.stt_bootstrap_limit else 100),
                "--language",
                args.stt_language,
                "--normalize",
            ],
            env_override=env,
        )

        if args.with_stt_train:
            _run(
                [
                    sys.executable,
                    "scripts/stt/train_whisper.py",
                    "--train-manifest",
                    str(REPO_ROOT / "data" / "raw" / "stt" / "manifest.train.csv"),
                    "--val-manifest",
                    str(REPO_ROOT / "data" / "raw" / "stt" / "manifest.val.csv"),
                    "--language",
                    args.stt_language,
                    "--normalize",
                    "--augment",
                ]
            )

    # Vision is optional/heavy.
    if args.with_vision:
        # Sentifargo vision training entrypoints can vary by dataset. If you have
        # a dedicated script, wire it here.
        candidate = REPO_ROOT / "scripts" / "run_train_vision.sh"
        if candidate.exists():
            _run(["bash", str(candidate)])
        else:
            print(
                "\n[train_all] --with-vision requested, but scripts/run_train_vision.sh not found; skipping."
            )

    if args.with_vision_full:
        candidate = REPO_ROOT / "scripts" / "train_all_vision_full.py"
        if candidate.exists():
            vision_max_train = int(args.vision_full_max_train) if int(args.vision_full_max_train) > 0 else 512
            vision_max_val = int(args.vision_full_max_val) if int(args.vision_full_max_val) > 0 else 128
            cmd = [
                sys.executable,
                str(candidate),
                "--device",
                str(args.vision_full_device),
                "--num-workers",
                "0",
                "--image-size",
                "160",
                "--progress-every",
                "2",
                "--probe-timeout-sec",
                "1.0",
                "--max-seconds-per-model",
                "1200",
                "--freeze-backbone",
                "--max-train",
                str(vision_max_train),
                "--max-val",
                str(vision_max_val),
            ]
            if not args.vision_full_pretrained:
                cmd.append("--no-pretrained")
            if int(args.vision_full_epochs) > 0:
                cmd.extend(["--epochs", str(int(args.vision_full_epochs))])
            if int(args.vision_full_batch_size) > 0:
                cmd.extend(["--batch-size", str(int(args.vision_full_batch_size))])
            _run(cmd)
        else:
            print(
                "\n[train_all] --with-vision-full requested, but scripts/train_all_vision_full.py not found; skipping."
            )

    if args.with_brand:
        # Prepare dataset (idempotent) and train YOLO detector.
        # Default to a fast local smoke-run (override via env vars for full training).
        os.environ.setdefault("BRAND_YOLO_MODEL", "yolov8n.pt")
        os.environ.setdefault("BRAND_EPOCHS", "1")
        os.environ.setdefault("BRAND_IMGSZ", "320")
        os.environ.setdefault("BRAND_BATCH", "8")
        os.environ.setdefault("BRAND_FRACTION", "0.1")
        os.environ.setdefault("BRAND_VAL", "false")
        os.environ.setdefault("BRAND_CACHE", "false")
        os.environ.setdefault("BRAND_DEVICE", "cpu")
        os.environ.setdefault("BRAND_WORKERS", "0")
        os.environ.setdefault("BRAND_TRAIN_MAX_IMAGES", "200")
        os.environ.setdefault("BRAND_VAL_MAX_IMAGES", "50")
        _run([sys.executable, "scripts/prepare_brand_data.py"])
        _run([sys.executable, "src/train/train_brand_logo_detector.py"])

    if args.with_video_temporal:
        # Trains a lightweight sklearn temporal model used by /api/vision/video/predict.
        _run([sys.executable, "src/train/train_video_temporal.py"])

    if args.with_face_emotion:
        # Trains a 7-class facial emotion classifier used by /api/vision/face_emotion/predict.
        _run(
            [
                sys.executable,
                "-m",
                "src.train.train_face_emotion",
                "--data-dir",
                str(args.face_emotion_data_dir),
            ]
        )

    print("\n✅ Training complete. Check experiments/*/metrics and models/* outputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
