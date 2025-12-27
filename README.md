# SentinelForge

SentinelForge is a **multimodal AI agent platform** that routes a single user request to the right subsystem (RAG, fraud/cyber/behavior scoring, recommendations, voice emotion, vision) and returns a **single structured response**: `{"route", "answer", "meta"}`.

The goal of this repository is not “a chatbot in a notebook”, but an end-to-end system that looks and feels like a service: **API, UI, training, monitoring, and a repeatable test gate**.

## What You Get
- **FastAPI gateway** (`uvicorn app.main:app`) that mounts chat + RAG + risk + recommender + vision + monitoring endpoints.
- **Streamlit command center UI** (`streamlit run app/streamlit_chatbot/app.py`) with chat, multimodal uploads, and dashboards.
- **Offline-first behavior** by default (local models + local RAG). Add `OPENAI_API_KEY` to enable LLM chat/streaming.
- **Training entrypoints** for core models + optional vision/YOLO/face-emotion (`scripts/train_all.py`, `src/train/*`).
- **Monitoring + drift summaries** with Prometheus metrics (`/metrics`) and JSONL event logs under `data/monitoring/logs/`.

## Architecture (At a Glance)

```mermaid
flowchart TD
  UI[Streamlit UI] --> API[FastAPI Gateway]
  API --> ORCH[Orchestrator]
  ORCH --> RAG[RAG (data/docs + embeddings)]
  ORCH --> RISK[Fraud/Cyber/Behavior + Fusion Risk]
  ORCH --> RECS[Recommender (text + multimodal)]
  ORCH --> VOICE[Voice Emotion + STT (optional)]
  ORCH --> VISION[Vision (image/video) + Face Emotion + Brand/Logo YOLO]
  API --> MON[Monitoring + Metrics]
```

Key entrypoints:
- **API**: `app/main.py`
- **UI**: `app/streamlit_chatbot/app.py`

For legacy modules and why they still exist, see `docs/LEGACY.md`.

## Quickstart (Local)

### 1) Install
Recommended: Python **3.11** (matches CI).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If you plan to use included LFS-tracked artifacts (e.g., `artifacts/brand/yolo_logo_det.pt`):
```bash
git lfs install
git lfs pull
```

### 2) Run API
```bash
uvicorn app.main:app --reload
```

### 3) Run UI
```bash
SENTINELFORGE_BACKEND=http://localhost:8000 streamlit run app/streamlit_chatbot/app.py
```
Use the left sidebar for navigation. The recommended chat view is **"✨ SentinelForge (Unified Chat)"** (legacy chat UIs are still available from the Chat page).

### One-command demo (backend + UI)
```bash
bash scripts/run_demo.sh
```

## Docker

### Dev compose (single container)
```bash
docker compose up --build
```

### Production compose (API + UI + Redis; optional monitoring/nginx)
```bash
cp .env.production.example .env
# edit .env (AUTH_TOKEN, CORS, ports, etc)

docker compose -f docker-compose.production.yml up -d --build

# Optional: monitoring (Prometheus/Grafana)
docker compose -f docker-compose.production.yml --profile monitoring up -d

# Optional: nginx reverse proxy (requires deploy/nginx/ssl certs)
docker compose -f docker-compose.production.yml --profile production up -d
```

See `docs/PRODUCTION_DEPLOYMENT.md` for a full deployment checklist.

## API (Quick Reference)

Most routes live under `/api/*`. If `AUTH_TOKEN` is set, send `Authorization: Bearer $AUTH_TOKEN`.

| Endpoint | What it does |
| --- | --- |
| `POST /api/chat` | Orchestrated chat (`message`/`text`) → `{route, answer, meta}` (+ `reply` for UI compatibility). |
| `POST /api/chat/multimodal` | Chat with optional `audio`/`image`/`video`; returns `meta.attachments` (voice/vision/face/STT). |
| `GET /api/chat/stream?message=...` | SSE streaming; uses OpenAI when `OPENAI_API_KEY` is set, otherwise streams the offline reply. |
| `POST /api/rag/query` | Retrieve passages from local docs (vector-store if available, TF-IDF fallback). |
| `POST /api/rag/ingest` / `POST /api/rag/upload` | Add docs to `data/docs/` and rebuild the local RAG index. |
| `POST /api/risk/analyze` | Risk “command center” scoring + decision + optional explanation + monitoring log. |
| `GET /api/monitor/summary` / `GET /api/monitor/drift` | Monitoring summaries + drift report (JSONL logs under `data/monitoring/logs/`). |
| `POST /api/recommend` | Recommendations (items) + MovieLens-style scoring + numeric-vector fallback. |
| `POST /api/recommend/multimodal` | Multimodal similarity (image/text). Falls back to an offline index on macOS if FAISS isn’t available. |
| `POST /api/voice/emotion` | Voice emotion label + confidence from an uploaded audio file. |
| `POST /api/stt/transcribe` | Speech-to-text (requires `faster-whisper`). |
| `POST /api/vision/predict` | Image classification (requires trained ResNet artifact). |
| `POST /api/vision/face_emotion/predict` | 7-class facial emotion (requires trained artifact). |
| `POST /api/vision/video/predict` | Video inference via sampled frames + temporal heuristics (requires `ffmpeg`). |
| `POST /api/vision/brand/predict` | YOLO logo/brand detector (requires `artifacts/brand/yolo_logo_det.pt`). |
| `GET /health` / `GET /health/detailed` / `GET /metrics` | Production health/readiness + Prometheus metrics. |

## Training (Practical)

Canonical entrypoints:
- `python scripts/train_all.py` (fraud/cyber/behavior/fusion + voice + recommender)
- `python scripts/train_all.py --with-brand` (brand/logo YOLO smoke-run by default; override env vars for full training)
- `python scripts/train_all.py --with-face-emotion` (7-class face emotion)
- `python scripts/train_all_vision.py` (vision wrapper; can be heavy depending on datasets)

Brand/logo YOLO (full control via env vars):
- Prepare dataset: `python scripts/prepare_brand_data.py`
- Train: `python -m src.train.train_brand_logo_detector`
- Tip for macOS: validation can be slow; set `BRAND_VAL=false` and/or `BRAND_VAL_MAX_IMAGES=2000`.

See `scripts/README.md` for the complete list.

## Testing / Quality
```bash
pytest -q
ruff check app tests
```

The CI workflow (`.github/workflows/ci.yml`) runs lint + a focused test set and builds the Docker image.

## Documentation
Start here: `docs/README.md`

## License
MIT (see `LICENSE`).
