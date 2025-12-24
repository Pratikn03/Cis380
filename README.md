# OmniChatX / Universal Anomaly Intelligence v2

## Overview (Narrative)
OmniChatX / Universal Anomaly Intelligence System (UAIS-V) is a multimodal AI agent platform that **routes one user request to the right subsystem** (RAG, fraud/risk scoring, recommendation, voice emotion, vision) and returns a **single structured response** with lineage/metadata.

It is not "just a chatbot". It's a **system-level AI stack** intended to look and behave like a production service:
- Real datasets and repeatable training scripts
- A central **agent orchestrator** that performs intent routing
- FastAPI endpoints for inference + monitoring
- Streamlit UI for interactive demos
- Tests + a one-command offline verification gate

## Why It Exists
Most applied AI capabilities are built as separate, isolated services (fraud detection, recommenders, vision models, voice emotion, and LLM chat). OmniChatX unifies them under one API surface so you can:
- Ask one question and get the correct tool routed automatically
- Log and monitor model behavior consistently
- Run a demo offline (with local models) and optionally enable an LLM later

## Architecture (5 Layers)
1) **Data layer** (realistic inputs)  
   - Raw datasets under `data/raw/` and domain docs under `docs/` / `data/docs/`
   - RAG embeddings under `data/embeddings/`
2) **Model layer** (core intelligence)  
   - Tabular models (fraud/cyber/behavior): scikit-learn + XGBoost/LightGBM/CatBoost (see `requirements.txt`)  
   - Recommender: offline MovieLens-style + explainability (`app/models/recommender/`)  
   - Voice emotion: MFCC/features + classifier (`app/models/voice/`)  
   - Vision: ResNet training/inference pipeline (`src/uais_v/` + `api/routes/vision.py` in the demo gateway)
3) **Agent/orchestration layer** (the "brain")  
   - Current gateway uses `agent/orchestrator.py` for `/api/chat` (rule-based + offline fallback).  
   - Next-gen structured orchestrator lives under `app/agent/*` and returns `{"route","answer","meta"}`.  
4) **API/serving layer** (FastAPI)  
   - Canonical entrypoint: `app/main.py` (re-exports `backend/main.py`).  
   - Gateway mounts both legacy `api/routes/*` and newer `app/api/*` routers (see `docs/LEGACY.md`).
5) **UI + testing + ops**  
   - Streamlit demo: `app/streamlit_chatbot/app.py` (Recommendations / Live Agent / Audio+Vision / Fraud+Monitoring)  
   - Test gate: `bash scripts/codex_test_all.sh` (runs unit tests + HTTP smoke tests)

## Current Phase
The core stack is built; the work now is "flagship polish":
- Make every capability visible in the UI (including voice + vision)
- Keep training + inference reproducible offline
- Keep docs and demo scripts aligned with the real entrypoints/endpoints

## Strength (Honest Assessment)
| Category | Assessment |
|---|---|
| Coursework / toy demo | No |
| Kaggle notebook | No |
| Internship-level system | Yes |
| Research-grade foundation | Yes (extensible multimodal platform) |
| Startup MVP | Yes (FastAPI + UI + monitoring + tests) |

## One-Paragraph Summary
OmniChatX (UAIS-V) is a multimodal AI agent system that integrates retrieval-augmented generation, fraud/risk scoring, recommendations, voice emotion recognition, and vision inference into a single orchestrated platform. It is built with real data pipelines, reproducible training scripts, FastAPI deployment, monitoring hooks, and a Streamlit demo UI so the full stack can be tested, monitored, and iterated like a production service.

## Section 1 — Project Identity
OmniChatX / Universal Anomaly Intelligence v2 is a multimodal AI agent platform driven by an orchestrator that routes incoming conversations to LLM-based chat, RAG, fraud/cyber/anomaly scoring, speech emotion recognition, and explainable recommendation services. The system ships with monitoring and drift-detection tooling, a Streamlit demo UI, and a CI/CD-backed Docker deployment so that the entire stack can be iterated like a production service.

## Section 2 — High-Level Architecture
* **FastAPI gateway (`app/main.py`)** re-exports the HTTP runtime in `backend/main.py` and mounts routers for chat, RAG, risk scoring, recommendation, voice, monitoring, vision, and health checks.
* **AI agent orchestrator** routes chat requests (current runtime: `agent/orchestrator.py`; next-gen structured orchestrator: `app/agent/*`).
* **Modular AI services** live under `app/api/`, `app/rag/`, `app/models/`, and `app/monitoring/`—each module (RAG retriever, fraud/cyber/behavior APIs, voice emotion predictor, explainable recommender, monitoring logger/drift) can be swapped or extended independently.
* **Streamlit UI and static frontend** (`app/streamlit_chatbot`, `ui/`) consume the orchestrator APIs to showcase chat, recommendation, risk overlays, and embeddings-driven RAG demos.
* **Docker + CI/CD** (`Dockerfile`, `docker-compose.yml`, `.github/workflows/ci.yml`) package the stack, run lint/tests, and build the production image as part of the pipeline.

**Request lifecycle:** user → FastAPI ingress → orchestrator decision engine → selected module (RAG, fraud/cyber/anomaly, recommender, voice, fallback chat) → module prediction + monitoring/logging → orchestrator aggregates answer + lineage → response returned. This agent-based routing keeps the stack flexible while tracing each step for observability.

## Section 3 — Core Features (What Is Implemented)
1. **AI Agent Orchestrator** (current runtime: `agent/orchestrator.py`) routes chat/risk/recs requests and supports offline fallback when `OPENAI_API_KEY` is missing. A structured next-gen orchestrator also exists under `app/agent/*`.
2. **Retrieval-Augmented Generation** (`app/rag/ingest.py`, `app/rag/retriever.py`, `app/rag/prompting.py`) ingests `docs/` content, builds TF-IDF embeddings, retrieves relevant chunks, and supplies `citations` to the orchestrator for transparent responses.
3. **Fraud / Cyber / Behavior Anomaly APIs** (`app/api/fraud.py`, `app/api/monitor.py` plus legacy `backend/api/*`) surface scoring from `models/fraud/`, `models/cyber/`, and `models/behavior/` artifacts, logging each invocation.
4. **Fraud Monitoring & Drift Detection** (`app/monitoring/`) append events to `data/monitoring/logs/fraud_events.jsonl`, compute freshness summaries, and expose summary/drift reports via `/api/monitor/summary` and `/api/monitor/drift`.
5. **Speech Emotion Recognition** (`app/models/voice/emotion_predict.py`, `app/api/voice.py`) extracts MFCC features, loads a local classifier (with a safe fallback model if the artifact is missing/incompatible), and returns an emotion label + confidence.
   - Supported emotion labels depend on the trained artifact’s `classes_` and the labels present in `data/raw/voice/*`.
6. **Explainable Recommendation Engine** (`app/models/recommender/` and `recommender/` packages) powers `/api/recommend` and `/api/recommend/explain`, supporting movie-style metadata, vectorized fallbacks, and text explanations.
7. **Streamlit Demo UI** (`app/streamlit_chatbot/app.py`) exposes Recommendations, Live Agent, Audio/Video/Vision, and Fraud/Cyber/Behavior (including monitoring logs) for a single-machine demo.
8. **Dockerized Deployment + CI**: `docker compose up --build` launches the service; `.github/workflows/ci.yml` uses Python 3.11, installs dependencies, runs `ruff` + `pytest`, and builds the Docker image to prevent regressions.
9. **Health & Metrics Endpoints**: `/health` (FastAPI and backend) reports uptime/version, while `backend/main.py` exposes `/metrics` for Prometheus, backed by request counters/histograms for latency tracking.

## Section 4 — Directory Structure
- `app/` — production FastAPI runtime that wires the orchestrator, routers, modular services, and monitoring helpers into a single process.
  - `app/api/` — router definitions for chat, RAG ingestion, fraud/risk, recommender, voice, monitoring, and health.
  - `app/agent/` — orchestrator, decision engine, and memory helpers that implement the agent-based routing logic.
  - `app/rag/` — ingestion, retrieval, and prompting utilities that power RAG responses and citations.
  - `app/models/` — ML helpers for recommender explainability, voice emotion extraction, and any shared feature utilities.
  - `app/monitoring/` — fraud log ingestion, baseline builder, drift calculator, and summary metrics.
- `ui/` — static demo assets (HTML, JS, CSS) served under `/ui` as an optional secondary experience.
- `data/` — datasets + persistent artifacts:
  - `data/raw/` (fraud/cyber/behavior/recommendation/voice/vision/nlp)
  - `data/docs/` (RAG corpus)
  - `data/embeddings/` (RAG index artifacts)
  - `data/monitoring/logs/` (`fraud_events.jsonl`, `risk_events.jsonl`)
- `tests/` — pytest suites that validate chat routing, RAG retrieval, and monitoring/drift tooling.
- `docs/` — architecture diagrams, component walkthroughs, and demos used to explain the architecture.

> Canonical FastAPI entrypoint: `app/main.py` (it re-exports the gateway in `backend/main.py` so both `uvicorn app.main:app` and `uvicorn backend.main:app` work).

## Section 5 — How to Run (Local)
1) Create and activate a Python 3.11 virtual environment.
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Start the FastAPI backend (canonical entrypoint).
```bash
uvicorn app.main:app --reload
```

3) Launch the Streamlit UI (uses backend at `http://localhost:8000` by default).
```bash
OMNICHATX_BACKEND=http://localhost:8000 streamlit run app/streamlit_chatbot/app.py
```
- Snapshot mic/webcam works out-of-the-box. WebRTC live streaming is **optional**—install extras with `pip install -r requirements-optional.txt` and toggle it in the UI.

4) Run tests (lightweight, no big artifacts required).
```bash
pytest -q
```

5) (Optional) Train models (writes to `models/` + `experiments/`).
```bash
# Core tabular + voice + recommender (fast-ish)
python scripts/train_all.py

# Brand/logo detector (requires ultralytics + LogoDet-3K prepared data)
python scripts/train_all.py --with-brand

# Full vision stack (deepfake + real/fake + video temporal; requires local datasets)
python scripts/train_all_vision.py

# Face emotion (7-class; requires an ImageFolder-style dataset)
# Expected: data/raw/vision/face_emotion/{train,val}/{angry,disgust,fear,happy,sad,surprise,neutral}/*
python -m src.train.train_face_emotion --data-dir data/raw/vision/face_emotion --epochs 5 --device auto
```

Notes:
- Canonical scripts are documented in `scripts/README.md`.
- Extra research scripts live under `scripts/experimental/`.

## Brand Recognition (LogoDet-3K → YOLOv8) Quickstart

This project supports **true brand recognition** via **logo detection** (YOLOv8) trained on datasets like **LogoDet-3K** and exported to `artifacts/brand/yolo_logo_det.pt`.

### 1) Put the dataset here (ignored by git)

- Place your raw LogoDet-3K dataset under:
   - `data/raw/brand/logodet3k/`

### 2) Convert to a unified YOLO dataset

The converter auto-detects COCO / Pascal VOC / YOLO layouts and produces:

- `data/processed/brand_yolo/images/{train,val}/...`
- `data/processed/brand_yolo/labels/{train,val}/...`
- `data/processed/brand_yolo/brands.yaml` (Ultralytics config)

```bash
python scripts/prepare_brand_data.py --src_root data/raw/brand/logodet3k --out_root data/processed/brand_yolo
```

### 3) Train YOLOv8 and export the artifact

Training copies the best weights to:

- `artifacts/brand/yolo_logo_det.pt`

```bash
python -m src.train.train_brand_logo_detector
```

Environment variables (optional):

- `BRAND_YOLO_MODEL` (default `yolov8s.pt`)
- `BRAND_EPOCHS` (default `50`)
- `BRAND_IMGSZ` (default `640`)
- `BRAND_BATCH` (default `16`)
- `BRAND_DEVICE` (default `auto` → `mps`/`cuda:0`/`cpu`)
- `BRAND_WORKERS` (default `4`)
- `BRAND_CACHE` (default `false`; set `disk` or `ram` to speed up dataloading)
- `BRAND_FRACTION` (default `1.0`; set `0.1` to train on 10% for a quick demo)
- `BRAND_PATIENCE` (default `100`)
- `BRAND_VAL` (default `true`; set `false` to skip validation during training — useful on macOS when NMS is slow)
- `BRAND_VAL_MAX_IMAGES` (default `0`; cap validation images for faster epochs, e.g. `2000`)
- `BRAND_TRAIN_MAX_IMAGES` (default `0`; cap training images for a quick smoke-run, e.g. `5000`)
- `BRAND_SEED` (default `42`; controls subset sampling when using `*_MAX_IMAGES`)

### 4) Predict via API

- Endpoint: `POST /api/vision/brand/predict`
- Upload: multipart form field `file`
- Returns: `{ detections: [{brand, confidence, bbox}], model_path }`

If the model wasn’t trained yet, the endpoint returns **503** with instructions.

### 5) Predict via Streamlit

Open the Streamlit UI and use the **Brand Recognition** tab. It uploads an image and draws bounding boxes over the predicted logos.

## Quick verification
```bash
bash scripts/test.sh
```

## One-command demo
```bash
bash scripts/run_demo.sh
```

## Section 6 — How to Run (Docker)
```bash
docker compose up --build
```
* Exposes port `8000` on the host.
* Health check: `curl http://localhost:8000/health` (mirrors the FastAPI health router defined in `app/api/health.py`).

## Section 7 — API Overview
| Endpoint | Description |
| --- | --- |
| `POST /api/chat` | Text chat; returns `{route, answer, meta}` (and `reply` for UI compatibility). |
| `POST /api/chat/multimodal` | Multipart chat with optional `audio`/`image`/`video`; attaches voice/vision/STT outputs into `meta.attachments`. |
| `POST /api/recommend/multimodal` | CLIP+FAISS multimodal similarity (image+text) over unified catalog (movies, electronics, courses). |
| `POST /api/recommend` | Item recommendations (`{user_id, top_k}` → `items`) and MovieLens-style scoring (`{user_id:int, movie_id:int}` → label/probability). |
| `POST /api/recommend/explain` | Explanation for `{user_id, item_id}` using `app/models/recommender/explain.py`. |
| `POST /api/rag/ingest` | Writes docs under `data/docs/`, rebuilds embeddings into `data/embeddings/`, and reports indexed chunk count. |
| `POST /api/voice/emotion` | Audio upload → MFCC features → emotion label + confidence (labels depend on the trained model). |
| `GET /api/monitor/summary` | Summarizes fraud/risk metrics and log paths under `data/monitoring/logs`. |
| `GET /api/monitor/events` | Tail of raw monitoring events (kind=`risk` or `fraud`). |
| `GET /api/monitor/drift` | Drift summaries vs. baseline (`app/monitoring/baseline.py`). |
| `GET /health` | Lightweight uptime/status ping; reports optional feature availability (STT, CLIP/FAISS, WebRTC). |

## Section 8 — Testing & Quality
* **Pytest** suites in `tests/` verify the orchestrator chat flow, document retriever, and monitoring stats. Run with `pytest tests/test_chat.py tests/test_rag.py tests/test_monitoring.py -q`.
* **CI pipeline** (`.github/workflows/ci.yml`) installs Python 3.11 dependencies, runs `ruff check app tests`, executes the same pytest suites, and builds the Docker image to keep linting, functionality, and containerization aligned.

## Section 9 — Project Status
### DONE
* FastAPI orchestrator and router stack under `app/` with modular services (chat, RAG, fraud/cyber/behavior, recommender, voice, monitoring).
* Streamlit demo UI plus static `/ui` alternative and health/metrics observability.
* Monitoring log ingestion, baseline/d drift detection, and Prometheus metrics in `backend/main.py`.
* Docker + GitHub Actions pipeline covering lint/test/build.

### PARTIAL / FUTURE
* RAG pipeline uses local embeddings + a lightweight vector store in `data/embeddings/`; swapping in a managed vector DB (Chroma/Pinecone) is a logical next step.
* Voice emotion prediction relies on a fallback logistic regression when no pretrained model is present; swapping in a production-grade model is ongoing work.
* Additional API guards (authentication tokens, rate limiting) and multi-agent orchestration policies can be layered on the existing decision engine.

### LEGACY / REFERENCE
* The top-level `agent/`, `api/`, `backend/`, `rag/`, `recommender/`, `scripts/`, `experiments/`, and `deploy/` directories keep previous implementations, training scripts, and utilities for reference but are not the default runtime.

## Section 10 — Who This Project Is For
* **ML Engineers** can study the modular training artifacts, joblib-backed models, and monitoring instrumentation before deploying new fraud/cyber/behavior predictors.
* **Applied AI Engineers** gain a working orchestrator, Streamlit UI, and API gateway to prototype new modules (RAG, recommender, voice) without rebuilding the stack.
* **AI Product Engineers** see how a single platform stitches together chat, monitoring, risk, and recommendations, which informs designing production features and instrumentation.
* **Data Scientists (production-focused)** benefit from the explainable recommender, monitoring/drift reports, and the CI-tested deployment path that proves experiments can ship.

## Section 11 — Final Note
This is a system-level AI project that prioritizes integration, monitoring, and production readiness; the orchestrator, Streamlit demos, and CI/Docker pipeline are engineered so multiservice intelligence can be tested, monitored, and deployed with confidence.

## Data & Artifacts (not in git)
- Large datasets, model weights, indexes, and archives are **ignored** (see `.gitignore`). Keep them under `data/`, `artifacts/`, `models/`, or `recommender/models/` locally.
- Use the provided scripts for preparation and indexing:
   - `scripts/prepare_brand_data.py` (LogoDet-3K → YOLO format)
   - `scripts/build_recommender_index.py` (CLIP+FAISS index over unified catalog)
   - `scripts/run_demo.sh` / `scripts/start_all.sh` for local demo

## 📚 Documentation

All documentation is organized under [`docs/`](docs/README.md):

| Category | Contents |
|----------|----------|
| **[docs/guides/](docs/guides/)** | How-to guides, installation, demos |
| **[docs/setup/](docs/setup/)** | Local setup, Git LFS configuration |
| **[docs/fixes/](docs/fixes/)** | Bug fixes and troubleshooting |
| **[docs/analysis/](docs/analysis/)** | Project analysis and cleanup reports |

**Quick Links:**
- [Production Deployment](docs/PRODUCTION_DEPLOYMENT.md)
- [Local Setup](docs/setup/local_run.md)
- [OmniChat Guide](docs/guides/OMNICHAT_COMPLETE.md)
- [Architecture](docs/architecture.md)
