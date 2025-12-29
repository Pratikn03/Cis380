# SentinelForge

SentinelForge is a production-ready multimodal AI command center that routes a
single user request to the right subsystem (risk, RAG, recommender, vision,
voice) and returns a structured response.

It is built to look and behave like a real service: API gateway, UI, training
pipelines, monitoring, and repeatable quality checks.

## What it can do
- Unified chat with text + image + audio + video attachments.
- Fraud, cyber, and behavior risk scoring with fused decisions.
- Brand/logo detection (YOLOv8) and face emotion analysis.
- Voice emotion classification from audio clips.
- Recommendations (numeric + MovieLens + multimodal similarity).
- RAG over local docs with offline-first embeddings.
- Monitoring logs and Prometheus metrics for production diagnostics.

## Table of contents
- Overview
- System architecture
- UI options
- Quickstart
- API quick reference
- Training and datasets
- Notebooks
- Monitoring and logs
- Configuration
- Deployment
- Project structure
- License

## Overview
SentinelForge is designed as a local-first AI platform that can run without any
external API keys. If you provide an `OPENAI_API_KEY`, streaming LLM responses
are enabled, but the default path stays fully offline.

Key entrypoints:
- API: `app/main.py`
- Streamlit UI: `app/streamlit_chatbot/app.py`
- Web UI: `ui-web/frontend`

## System architecture

```mermaid
flowchart TD
  UI[Streamlit UI] --> API[FastAPI Gateway]
  WEB[Web UI] --> API
  API --> ORCH[Orchestrator]
  ORCH --> RAG[RAG (data/docs + embeddings)]
  ORCH --> RISK[Fraud/Cyber/Behavior + Fusion Risk]
  ORCH --> RECS[Recommender (text + multimodal)]
  ORCH --> VOICE[Voice Emotion + STT (optional)]
  ORCH --> VISION[Vision (image/video) + Face Emotion + Brand/Logo YOLO]
  API --> MON[Monitoring + Metrics]
```

## UI options

### 1) Streamlit Command Center
```bash
SENTINELFORGE_BACKEND=http://localhost:8000 streamlit run app/streamlit_chatbot/app.py
```

### 2) SentinelForge Web UI (React + Tailwind)
```bash
cd ui-web/frontend
cp .env.example .env
npm install
npm run dev
```

For GitHub Pages deployment, see `ui-web/deploy/github-pages.md`.

## Quickstart (local)

### 1) Install
Recommended: Python 3.11.
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If you plan to use LFS artifacts (for example, brand YOLO weights):
```bash
git lfs install
git lfs pull
```

### 2) Run API
```bash
uvicorn app.main:app --reload
```

### 3) Run UI (choose one)
- Streamlit UI: `streamlit run app/streamlit_chatbot/app.py`
- Web UI: `npm run dev` in `ui-web/frontend`

### One-command demo (backend + Streamlit UI)
```bash
bash scripts/run_demo.sh
```

## API quick reference

Most routes live under `/api/*`. If `AUTH_TOKEN` is set, send
`Authorization: Bearer $AUTH_TOKEN`.

| Endpoint | What it does |
| --- | --- |
| `POST /api/chat` | Orchestrated chat with `{route, answer, meta}`. |
| `POST /api/chat/multimodal` | Chat with optional audio/image/video; attaches voice/vision results. |
| `GET /api/chat/stream?message=...` | SSE streaming (uses OpenAI if `OPENAI_API_KEY` is set). |
| `POST /api/rag/query` | Retrieve passages from local docs. |
| `POST /api/rag/ingest` / `POST /api/rag/upload` | Ingest docs into `data/docs/` and rebuild embeddings. |
| `POST /api/risk/analyze` | Fused fraud/cyber/behavior scoring + decision. |
| `POST /api/fraud` / `POST /api/cyber` / `POST /api/behavior` | Domain scoring endpoints. |
| `POST /api/recommend` | Recommendations from the baseline model. |
| `POST /api/recommend/multimodal` | Multimodal similarity (image/text). |
| `POST /api/voice/emotion` | Voice emotion prediction from audio upload. |
| `POST /api/stt/transcribe` | Speech-to-text (requires `faster-whisper`). |
| `POST /api/vision/predict` | Image classification (requires trained artifact). |
| `POST /api/vision/face_emotion/predict` | Face emotion prediction. |
| `POST /api/vision/video/predict` | Video inference (requires `ffmpeg`). |
| `POST /api/vision/brand/predict` | Brand/logo YOLO detector. |
| `GET /health` / `GET /health/detailed` / `GET /metrics` | Production health/readiness + Prometheus metrics. |

## Training and datasets

Use `scripts/train_all.py` for the core training bundle, or run individual
trainers from `src/train/`. Dataset expectations live in the notebooks, plus
`configs/data_*.yaml`.

| Module | Training entrypoint | Artifact |
| --- | --- | --- |
| Fraud | `python -m src.train.train_fraud` | `models/fraud/*.pkl` |
| Cyber | `python -m src.train.train_cyber` | `models/cyber/*.pkl` |
| Behavior | `python -m src.train.train_behavior` | `models/behavior/*.pkl` |
| Face emotion | `python -m src.train.train_face_emotion` | `models/vision/face_emotion/` |
| Brand/logo YOLO | `python -m src.train.train_brand_logo_detector` | `artifacts/brand/yolo_logo_det.pt` |
| Voice emotion | `python app/models/voice/emotion_train.py` | `models/voice_emotion.pkl` |
| Video temporal | `python -m src.train.train_video_temporal` | `models/vision/video_temporal_model.pkl` |
| MovieLens recommender | `python -m src.train.train_movielens_recommender` | `models/recommender/` |
| Multimodal index | `python scripts/build_recommender_index.py` | `data/embeddings/` |

## Notebooks

Start with the index notebook:
- `notebooks/overview/00_notebook_index.ipynb`

It links every training, EDA, and evaluation notebook and provides a map of the
full project. New training notebooks (81-88) include dataset inventory, code
links, and visuals.

## Monitoring and logs
- Prometheus metrics: `/metrics`
- Health endpoints: `/health`, `/health/live`, `/health/ready`, `/health/detailed`
- Event logs: `data/monitoring/logs/*.jsonl`

## Configuration

Important environment variables:
- `AUTH_TOKEN` for API auth (Bearer token).
- `OPENAI_API_KEY` to enable LLM streaming.
- `CORS_ORIGINS` for production CORS configuration.
- `SENTINELFORGE_BACKEND` for Streamlit/Web UI backend URL.

See `.env.example` and `.env.production.example` for templates.

## Deployment

Docker:
```bash
docker compose up --build
```

Production compose (API + UI + optional monitoring):
```bash
cp .env.production.example .env
docker compose -f docker-compose.production.yml up -d --build
```

See `docs/PRODUCTION_DEPLOYMENT.md` for deployment details.

## Project structure

```
app/                    FastAPI + Streamlit UI
app/legacy/             Legacy API modules used by app/main.py
ui-web/                 React + Tailwind web UI
src/                    Training and model code
scripts/                Data prep + training entrypoints
configs/                Dataset and model configs
notebooks/              EDA, training, evaluation, overview
docs/                   Documentation
```

## License
MIT. See `LICENSE`.
