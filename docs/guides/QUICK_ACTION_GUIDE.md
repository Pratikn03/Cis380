# Quick Actions (Developer Cheatsheet)

Copy/paste commands that are commonly used during development.

## Install + Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload
SENTINELFORGE_BACKEND=http://localhost:8000 streamlit run app/streamlit_chatbot/app.py
```

## Test Gate

```bash
pytest -q
ruff check app tests
```

## One-command Demo

```bash
bash scripts/run_demo.sh
```

## Train Core Models

```bash
python scripts/train_all.py
```

## Brand/logo YOLO (Fast Smoke Run)

```bash
BRAND_YOLO_MODEL=yolov8n.pt \
BRAND_EPOCHS=1 \
BRAND_IMGSZ=320 \
BRAND_FRACTION=0.1 \
BRAND_VAL=false \
python -m src.train.train_brand_logo_detector
```

## Production Readiness Check

```bash
python scripts/check_production.py
```

