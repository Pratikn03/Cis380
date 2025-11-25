#!/usr/bin/env bash
set -euo pipefail
python - <<'PY'
from pathlib import Path

from uais_v.models.vision_resnet import VisionConfig
from uais_v.training.train_vision import VisionTrainConfig, train_resnet_classifier

vision_cfg = VisionConfig()
train_cfg = VisionTrainConfig()

data_dir = Path('data/processed/vision')
if not (data_dir / 'train').exists():
    print('Vision data not found at', data_dir, '- please add train/ and val/ folders. Skipping.')
else:
    save_dir = Path('models/vision/resnet')
    _, metrics, out_dir = train_resnet_classifier(data_dir, vision_cfg, train_cfg, save_dir=save_dir)
    print('Vision metrics:', metrics)
PY
