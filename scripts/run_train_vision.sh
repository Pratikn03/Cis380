#!/usr/bin/env bash
set -euo pipefail

# macOS note:
# - This script used to run an inline `python - <<'PY'` with DataLoader workers >0,
#   which can crash under multiprocessing spawn (sys.argv[0] becomes "<stdin>").
# - Default to num_workers=0 for stability; override via VISION_NUM_WORKERS.

python - <<'PY'
from pathlib import Path

from uais_v.models.vision_resnet import VisionConfig
from uais_v.training.train_vision import VisionTrainConfig, train_resnet_classifier

import os

vision_cfg = VisionConfig(
    num_classes=2,
    pretrained=True,
)
train_cfg = VisionTrainConfig(
    batch_size=int(os.getenv("VISION_BATCH_SIZE", "16")),
    epochs=int(os.getenv("VISION_EPOCHS", "3")),
    num_workers=int(os.getenv("VISION_NUM_WORKERS", "0")),
    lr=float(os.getenv("VISION_LR", "0.001")),
    max_batches_per_epoch=int(os.getenv("VISION_MAX_BATCHES_PER_EPOCH", "0")) or None,
)

data_dir = Path('data/processed/vision')
if not (data_dir / 'train').exists():
    print('Vision data not found at', data_dir, '- please add train/ and val/ folders. Skipping.')
else:
    save_dir = Path('models/vision/resnet')
    _, metrics, out_dir = train_resnet_classifier(data_dir, vision_cfg, train_cfg, save_dir=save_dir)
    # Persist class names so the API can map logits -> labels deterministically.
    try:
        from torchvision.datasets import ImageFolder

        classes = ImageFolder(data_dir / "train").classes
        (save_dir / "classes.txt").write_text("\n".join(classes) + "\n", encoding="utf-8")
        print("Saved vision classes to", save_dir / "classes.txt")
    except Exception as exc:
        print("WARN: could not save classes.txt:", exc)
    print('Vision metrics:', metrics)
PY
