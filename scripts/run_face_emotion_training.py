"""
Script to prepare dummy data (if needed) and run face emotion training.
"""

import os
import sys
import random
from pathlib import Path
from PIL import Image
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data/raw/vision/face_emotion"
MODEL_DIR = ROOT / "models/vision/face_emotion"


def create_dummy_data():
    print(f"Ensuring face emotion data at {DATA_DIR}...")
    # Added "contempt" as a new class
    emotions = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral", "contempt"]

    # Create train and val splits
    for split in ["train", "val"]:
        for emotion in emotions:
            dir_path = DATA_DIR / split / emotion
            if dir_path.exists() and any(dir_path.iterdir()):
                continue

            dir_path.mkdir(parents=True, exist_ok=True)

            # Create a few dummy images
            num_images = 20 if split == "train" else 5
            for i in range(num_images):
                # Random color image
                color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                img = Image.new("RGB", (48, 48), color=color)
                img.save(dir_path / f"{emotion}_{i}.jpg")


def run_training():
    print("Running training script...")
    # Ensure ROOT is in PYTHONPATH
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")

    cmd = [
        sys.executable,
        "-m",
        "src.train.train_face_emotion",
        "--data-dir",
        str(DATA_DIR),
        "--out-dir",
        str(MODEL_DIR),
        "--epochs",
        "2",
        "--batch-size",
        "8",
        "--image-size",
        "48",
        "--arch",
        "small_cnn",
    ]

    try:
        subprocess.run(cmd, cwd=str(ROOT), check=True, env=env)
        print(f"\n✅ Model artifact generated at: {MODEL_DIR / 'model.pt'}")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Training failed with exit code {e.returncode}")
        sys.exit(e.returncode)


if __name__ == "__main__":
    create_dummy_data()
    run_training()
