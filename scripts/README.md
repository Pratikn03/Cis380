## Scripts

This repository has a **single canonical UI + training entrypoints**.

### Canonical entrypoints

- **Run demo (backend + UI):** `bash scripts/run_demo.sh`
- **Train core models:** `python scripts/train_all.py`
- **Train vision stack:** `python scripts/train_all_vision.py`
- **Train face emotion (image):** `python -m src.train.train_face_emotion --data-dir data/raw/vision/face_emotion`
- **Production readiness check:** `python scripts/check_production.py`

### Experimental scripts

Experimental / research scripts live under `scripts/experimental/`.

- They may require large local datasets, GPU acceleration, or extra Python deps.
- They are **not** used by the production Docker images by default.
