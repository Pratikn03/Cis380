# Streamlit UI Guide (SentinelForge)

SentinelForge ships with a Streamlit “command center” UI that exercises most of the FastAPI endpoints from one place.

UI entrypoint: `app/streamlit_chatbot/app.py`

## Run It

### Option A: One-command demo
```bash
bash scripts/run_demo.sh
```

### Option B: Two terminals

Terminal 1 (API):
```bash
uvicorn app.main:app --reload --port 8000
```

Terminal 2 (UI):
```bash
export SENTINELFORGE_BACKEND="http://localhost:8000"
streamlit run app/streamlit_chatbot/app.py
```

## Environment Variables
- `SENTINELFORGE_BACKEND` — FastAPI base URL (default is `http://localhost:8000`)
- `AUTH_TOKEN` — if set, the UI sends `Authorization: Bearer $AUTH_TOKEN`

## Tabs / Pages (What to Show)

The UI is organized as top-level tabs:
- **Unified chat (“all‑in‑one”)**: single chat surface with multimodal uploads and tool routing.
- **Classic chat UI**: layout variant useful for testing frontend behaviors.
- **Recommendations**: text recommendations and multimodal similarity.
- **Live Agent**: direct calls to `/api/chat` and `/api/chat/multimodal`.
- **Audio/Video/Vision**: upload media and inspect model outputs.
- **Fraud/Cyber/Behavior**: risk simulation and raw model scoring.
- **Metrics**: health and Prometheus metrics links.

## What “Offline” Means Here

SentinelForge can run without any external LLM:
- If `OPENAI_API_KEY` is **unset**, `/api/chat` uses an offline response path plus local RAG.
- If `OPENAI_API_KEY` is **set**, chat routes may call OpenAI (see `app/legacy/agent/orchestrator.py`).

## Common Issues

### UI can’t reach backend
- Confirm `SENTINELFORGE_BACKEND` points to the running API.
- Check API health: `curl http://localhost:8000/health`

### “503 … model not trained”
Some endpoints require local model artifacts (not committed to git). Train the missing model and try again:
- `python scripts/train_all.py` (core)
- `python scripts/train_all.py --with-face-emotion`
- `python scripts/prepare_brand_data.py && python -m src.train.train_brand_logo_detector`

### Brand/logo YOLO training is slow on macOS
Validation can be slow (NMS warnings). For a quick system check:
- use a smaller model (`BRAND_YOLO_MODEL=yolov8n.pt`)
- use smaller images (`BRAND_IMGSZ=320`)
- disable validation (`BRAND_VAL=false`)
- train on a fraction (`BRAND_FRACTION=0.1`)
