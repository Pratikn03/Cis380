# Artifacts

This directory contains **runtime artifacts** that are not produced by the application itself (e.g., trained weights).

Notes:
- Large binaries (e.g., `.pt`, `.pkl`, `.npy`) are tracked via **Git LFS** (see `docs/setup/GIT_LFS_SETUP.md`).
- For a fresh clone, run `git lfs install` once and `git lfs pull` to download any required weights.

## Included artifacts

- `artifacts/brand/yolo_logo_det.pt`: YOLOv8 logo detector used by `POST /api/vision/brand/predict`.

## Generate your own

If you prefer not to use the included weights, you can train locally:

- Prepare dataset: `python scripts/prepare_brand_data.py`
- Train: `python -m src.train.train_brand_logo_detector`

