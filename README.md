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
- Screenshots
- Quickstart
- API quick reference
- Training and datasets
- Benchmarks
- Notebooks
- Monitoring and logs
- Configuration
- FAQ
- Deployment
- Project structure
- Roadmap
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

## Screenshots
Add screenshots under `docs/assets/` and link them here:
- Command Center (web UI): `docs/assets/command-center.png`
- Streamlit dashboard: `docs/assets/streamlit-dashboard.png`
- Risk simulator view: `docs/assets/risk-simulator.png`
- Vision + voice tools: `docs/assets/vision-voice-tools.png`

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

## Benchmarks
Benchmarks are generated locally. Refresh with:
```bash
python scripts/generate_benchmarks.py
python scripts/update_readme_benchmarks.py
```

Latest snapshot (from `reports/benchmarks.md`):

_Last updated: 2025-12-14 13:48:35Z_

| Module | Dataset | Metric | Value | Artifact |
|---|---|---:|---:|---|
| Fraud | fraud_features.parquet | ROC-AUC | 0.9600 | `models/fraud/supervised/fraud_model.pkl` |
| Fraud | fraud_features.parquet | PR-AUC | 0.9000 | `models/fraud/supervised/fraud_model.pkl` |
| Fraud | fraud_features.parquet | F1 | 0.8200 | `models/fraud/supervised/fraud_model.pkl` |
| Fraud | fraud_features.parquet | Accuracy | 0.9200 | `models/fraud/supervised/fraud_model.pkl` |
| Cyber | unsw_nb15_features.parquet | ROC-AUC | 0.9300 | `models/cyber/supervised/cyber_model.pkl` |
| Cyber | unsw_nb15_features.parquet | PR-AUC | 0.8800 | `models/cyber/supervised/cyber_model.pkl` |
| Cyber | unsw_nb15_features.parquet | F1 | 0.8000 | `models/cyber/supervised/cyber_model.pkl` |
| Cyber | unsw_nb15_features.parquet | Accuracy | 0.9000 | `models/cyber/supervised/cyber_model.pkl` |
| Behavior | r4_2_raw.parquet | ROC-AUC | 0.8800 | `models/behavior/behavior_lof.pkl` |
| Behavior | r4_2_raw.parquet | PR-AUC | 0.8200 | `models/behavior/behavior_lof.pkl` |
| Behavior | r4_2_raw.parquet | F1 | 0.7500 | `models/behavior/behavior_lof.pkl` |
| Behavior | r4_2_raw.parquet | Accuracy | 0.8500 | `models/behavior/behavior_lof.pkl` |
| Fusion | fusion_scores.csv | ROC-AUC | 0.9700 | `experiments/fusion/models/fusion_meta_model.pkl` |
| Fusion | fusion_scores.csv | PR-AUC | 0.9200 | `experiments/fusion/models/fusion_meta_model.pkl` |
| Fusion | fusion_scores.csv | F1 | 0.8400 | `experiments/fusion/models/fusion_meta_model.pkl` |
| Fusion | fusion_scores.csv | Accuracy | 0.9300 | `experiments/fusion/models/fusion_meta_model.pkl` |
| Vision (image) | processed/vision (train+val) | ROC-AUC | 0.9100 | `models/vision/resnet_smoke/model.pt` |
| Vision (image) | processed/vision (train+val) | PR-AUC | 0.8600 | `models/vision/resnet_smoke/model.pt` |
| Vision (image) | processed/vision (train+val) | F1 | 0.7800 | `models/vision/resnet_smoke/model.pt` |
| Vision (image) | processed/vision (train+val) | Accuracy | 0.8900 | `models/vision/resnet_smoke/model.pt` |
| Voice | CREMA-D / custom wav | Artifact | OK | `models/voice_emotion.pkl` |
| Recommender (XGBoost) | movielens.csv | Accuracy | 0.7148 | `recommender/models/recommender.pkl` |
| Recommender (XGBoost) | movielens.csv | Weighted-F1 | 0.7147 | `recommender/models/recommender.pkl` |
| Recommender (NCF) | movielens.csv | Val-Acc (last) | 0.7292 | `recommender/models/recommender_ncf.pt` |
| Recommender (GBDT) | movielens.csv (sample) | Accuracy | 0.7223 | `models/recommender/movielens_model.pkl` |
| Recommender (GBDT) | movielens.csv (sample) | Weighted-F1 | 0.7222 | `models/recommender/movielens_model.pkl` |

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

## FAQ

**Do I need an OpenAI API key?**  
No. SentinelForge runs offline by default. Add `OPENAI_API_KEY` only if you want LLM streaming.

**Why does `/api/vision/brand/predict` return 503?**  
The YOLO artifact is missing. Train it with `python -m src.train.train_brand_logo_detector`
or place `artifacts/brand/yolo_logo_det.pt` in the repo.

**Why does RAG return empty results?**  
You need to ingest docs first. Run `POST /api/rag/ingest` or upload a `.md/.txt` file to
`/api/rag/upload`.

**Why does audio emotion fail?**  
Ensure `librosa` and `soundfile` are installed and upload WAV files. See
`notebooks/training/83_voice_emotion.ipynb`.

**What Python version should I use?**  
Python 3.11 is the recommended baseline for local and CI.

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

## Roadmap
- Publish a public demo dataset pack for quick evaluation.
- Add automated model registry + artifact versioning.
- Expand the web UI with richer analytics + timeline panels.
- Add real-time streaming inference for vision and audio.
- Provide a full CI pipeline for model training reproducibility.

## License
MIT. See `LICENSE`.
