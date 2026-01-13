# SentinelForge



[![CI](https://github.com/Pratikn03/Cis380/actions/workflows/ci.yml/badge.svg)](https://github.com/Pratikn03/Cis380/actions/workflows/ci.yml)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)**SentinelForge** is a comprehensive risk intelligence platform for fraud detection, cybersecurity monitoring, and behavioral analytics.SentinelForge is a **multimodal AI agent platform** that routes a single user request to the right subsystem (RAG, fraud/cyber/behavior scoring, recommendations, voice emotion, vision) and returns a **single structured response**: `{"route", "answer", "meta"}`.

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)



**SentinelForge** is a **production-grade multimodal AI platform** for enterprise anomaly detection, combining fraud detection, cybersecurity monitoring, behavioral analytics, voice emotion analysis, and computer vision into a unified intelligence system.

## 🌐 Live DemoThe goal of this repository is not “a chatbot in a notebook”, but an end-to-end system that looks and feels like a service: **API, UI, training, monitoring, and a repeatable test gate**.

## 🌐 Live Demo



**[View Live Demo →](https://pratikn03.github.io/Cis380/)**

**[View Live Demo →](https://pratikn03.github.io/Cis380/)**## What You Get

## ✨ Key Features

- **FastAPI gateway** (`uvicorn app.main:app`) that mounts chat + RAG + risk + recommender + vision + monitoring endpoints.

| Domain | Capabilities |

|--------|-------------|## Features- **Streamlit command center UI** (`streamlit run app/streamlit_chatbot/app.py`) with chat, multimodal uploads, and dashboards.

| **Fraud Detection** | Transaction scoring, velocity analysis, synthetic fraud generation |

| **Cybersecurity** | Network intrusion detection (UNSW-NB15), attack timeline visualization |- **Offline-first behavior** by default (local models + local RAG). Add `OPENAI_API_KEY` to enable LLM chat/streaming.

| **Behavior Analytics** | User session modeling, insider threat detection, anomaly scoring |

| **Voice Intelligence** | Emotion recognition, stress detection, speech-to-text |- **Risk Analysis** - Real-time fraud and cyber threat detection- **Training entrypoints** for core models + optional vision/YOLO/face-emotion (`scripts/train_all.py`, `src/train/*`).

| **Computer Vision** | Image classification, video analysis, facial emotion, brand detection |

| **RAG System** | Document ingestion, semantic search, multi-strategy chunking |- **Behavioral Monitoring** - User behavior pattern analysis- **Monitoring + drift summaries** with Prometheus metrics (`/metrics`) and JSONL event logs under `data/monitoring/logs/`.

| **Recommendations** | Collaborative filtering, multimodal similarity (MovieLens) |

- **Voice Analytics** - Emotion detection from audio

## 🏗️ Architecture

- **Vision Processing** - Image and video analysis for security## Architecture (At a Glance)

```

┌─────────────────────────────────────────────────────────────────────────┐- **Dashboard** - Interactive command center UI

│                         SentinelForge Platform                          │

├─────────────────────────────────────────────────────────────────────────┤```mermaid

│  Layer 1: Interface                                                     │

│  ├── Streamlit UI (app/streamlit_chatbot/)                              │## Architectureflowchart TD

│  ├── React Frontend (ui-web/frontend/)                                  │

│  └── REST API (FastAPI)                                                 │  UI[Streamlit UI] --> API[FastAPI Gateway]

├─────────────────────────────────────────────────────────────────────────┤

│  Layer 2: Orchestration                                                 │```  API --> ORCH[Orchestrator]

│  └── Intent Router → Domain Routing → Response Fusion                   │

├─────────────────────────────────────────────────────────────────────────┤┌─────────────────────────────────────────────────────────────┐  ORCH --> RAG[RAG (data/docs + embeddings)]

│  Layer 3: Intelligence Engines                                          │

│  ├── Fraud Engine    │  Cyber Engine   │  Behavior Engine              ││                    SentinelForge Platform                    │  ORCH --> RISK[Fraud/Cyber/Behavior + Fusion Risk]

│  ├── Voice Engine    │  Vision Engine  │  RAG Engine                   │

│  └── Recommender     │  Fusion Layer   │  Confidence Scoring           │├─────────────────────────────────────────────────────────────┤  ORCH --> RECS[Recommender (text + multimodal)]

├─────────────────────────────────────────────────────────────────────────┤

│  Layer 4: MLOps                                                         ││  Frontend         │  React + TypeScript + Tailwind CSS      │  ORCH --> VOICE[Voice Emotion + STT (optional)]

│  └── Model Registry │ Experiment Tracking │ A/B Testing │ Monitoring   │

└─────────────────────────────────────────────────────────────────────────┘├───────────────────┼─────────────────────────────────────────┤  ORCH --> VISION[Vision (image/video) + Face Emotion + Brand/Logo YOLO]

```

│  Backend          │  FastAPI + Python                       │  API --> MON[Monitoring + Metrics]

For detailed architecture documentation, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

├───────────────────┼─────────────────────────────────────────┤```

## 🚀 Quick Start

│  Models           │  Fraud, Cyber, Behavior, Voice, Vision  │

### Prerequisites

- Python 3.11+ (matches CI)├───────────────────┼─────────────────────────────────────────┤Key entrypoints:

- Node.js 18+ (for React frontend)

│  Database         │  Vector Store + Document Index          │- **API**: `app/main.py`

### Installation

└───────────────────┴─────────────────────────────────────────┘- **UI**: `app/streamlit_chatbot/app.py`

```bash

# Clone and setup```

git clone https://github.com/Pratikn03/Cis380.git

cd Cis380For legacy modules and why they still exist, see `docs/LEGACY.md`.



# Create virtual environment## Quick Start

python3 -m venv .venv

source .venv/bin/activate## Quickstart (Local)



# Install dependencies### Prerequisites

pip install -r requirements.txt

- Python 3.11+### 1) Install

# Pull LFS artifacts (optional, for pre-trained models)

git lfs install- Node.js 18+Recommended: Python **3.11** (matches CI).

git lfs pull

```



### Run API### Installation```bash



```bashpython3 -m venv .venv

uvicorn app.main:app --reload --port 8000

``````bashsource .venv/bin/activate



### Run UI# Clone repositorypip install -r requirements.txt



```bashgit clone https://github.com/Pratikn03/Cis380.git```

SENTINELFORGE_BACKEND=http://localhost:8000 streamlit run app/streamlit_chatbot/app.py

```cd Cis380



### One-command DemoIf you plan to use included LFS-tracked artifacts (e.g., `artifacts/brand/yolo_logo_det.pt`):



```bash# Setup Python environment```bash

bash scripts/run_demo.sh

```python3 -m venv .venvgit lfs install



## 🐳 Dockersource .venv/bin/activategit lfs pull



### Developmentpip install -r requirements.txt```



```bash

docker compose up --build

```# Start backend### 2) Run API



### Productionuvicorn app.main:app --reload --port 8000```bash



```bash```uvicorn app.main:app --reload

cp .env.production.example .env

# Edit .env (AUTH_TOKEN, CORS, ports, etc.)```



docker compose -f docker-compose.production.yml up -d --build### Frontend Development



# Optional: monitoring (Prometheus/Grafana)### 3) Run UI

docker compose -f docker-compose.production.yml --profile monitoring up -d

``````bash```bash



See [docs/PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md) for full deployment checklist.cd ui-web/frontendSENTINELFORGE_BACKEND=http://localhost:8000 streamlit run app/streamlit_chatbot/app.py



## 📡 API Referencenpm install```



Most routes live under `/api/*`. If `AUTH_TOKEN` is set, send `Authorization: Bearer $AUTH_TOKEN`.npm run devUse the left sidebar for navigation. The recommended chat view is **"✨ SentinelForge (Unified Chat)"** (legacy chat UIs are still available from the Chat page).



| Endpoint | Description |```

|----------|-------------|

| `POST /api/chat` | Orchestrated chat → `{route, answer, meta}` |### One-command demo (backend + UI)

| `POST /api/chat/multimodal` | Chat with audio/image/video attachments |

| `GET /api/chat/stream` | SSE streaming (OpenAI or offline) |## API Endpoints```bash

| `POST /api/rag/query` | Retrieve passages from document store |

| `POST /api/rag/upload` | Ingest documents into RAG index |bash scripts/run_demo.sh

| `POST /api/risk/analyze` | Risk scoring + decision + explanation |

| `POST /api/fraud` | Fraud detection analysis || Endpoint | Description |```

| `POST /api/cyber` | Cybersecurity threat analysis |

| `POST /api/behavior` | Behavioral pattern analysis ||----------|-------------|

| `POST /api/recommend` | Recommendation engine |

| `POST /api/voice/emotion` | Voice emotion detection || `POST /api/risk/analyze` | Risk assessment scoring |## Docker

| `POST /api/vision/predict` | Image classification |

| `POST /api/vision/face_emotion/predict` | Facial emotion recognition || `POST /api/fraud` | Fraud detection |

| `POST /api/vision/video/predict` | Video analysis |

| `GET /health` | System health check || `POST /api/cyber` | Cybersecurity analysis |### Dev compose (single container)

| `GET /metrics` | Prometheus metrics |

| `POST /api/behavior` | Behavioral pattern analysis |```bash

## 🧪 Training

| `POST /api/voice/emotion` | Voice emotion detection |docker compose up --build

```bash

# Train all core models (fraud, cyber, behavior, fusion)| `GET /health` | System health check |```

python scripts/train_all.py



# Include vision models

python scripts/train_all.py --with-brand --with-face-emotion## Project Structure### Production compose (API + UI + Redis; optional monitoring/nginx)



# Individual training```bash

python -m src.train.train_fraud

python -m src.train.train_cyber```cp .env.production.example .env

python -m src.train.train_behavior

```├── app/                    # Backend application# edit .env (AUTH_TOKEN, CORS, ports, etc)



See [scripts/README.md](scripts/README.md) for complete training documentation.│   ├── api/               # API routes



## ✅ Testing & Quality│   ├── models/            # ML model interfacesdocker compose -f docker-compose.production.yml up -d --build



```bash│   └── services/          # Business logic

# Run tests

pytest -q├── ui-web/frontend/       # React frontend# Optional: monitoring (Prometheus/Grafana)



# Run with coverage├── models/                # Trained model artifactsdocker compose -f docker-compose.production.yml --profile monitoring up -d

pytest --cov=app --cov=src --cov-report=html

├── data/                  # Datasets and embeddings

# Linting

ruff check app tests src└── docs/                  # Documentation# Optional: nginx reverse proxy (requires deploy/nginx/ssl certs)



# Type checking```docker compose -f docker-compose.production.yml --profile production up -d

mypy app src --ignore-missing-imports

``````



## 📊 Benchmarks## Technology Stack



Run end-to-end evaluation benchmarks:See `docs/PRODUCTION_DEPLOYMENT.md` for a full deployment checklist.



```bash- **Frontend**: React 18, TypeScript, Tailwind CSS, Vite

python benchmarks/benchmark_suite.py

```- **Backend**: FastAPI, Python 3.11, Pydantic## API (Quick Reference)



See [benchmarks/README.md](benchmarks/README.md) for benchmark documentation.- **ML**: scikit-learn, PyTorch, XGBoost



## 📁 Project Structure- **Infrastructure**: Docker, GitHub ActionsMost routes live under `/api/*`. If `AUTH_TOKEN` is set, send `Authorization: Bearer $AUTH_TOKEN`.



```

├── app/                    # FastAPI application

│   ├── api/               # API routes## Deployment| Endpoint | What it does |

│   ├── models/            # Request/response models

│   ├── services/          # Business logic| --- | --- |

│   ├── streamlit_chatbot/ # Streamlit UI

│   └── monitoring/        # Metrics & alertingThe frontend automatically deploys to GitHub Pages on push to `main`.| `POST /api/chat` | Orchestrated chat (`message`/`text`) → `{route, answer, meta}` (+ `reply` for UI compatibility). |

├── src/                    # Core ML modules

│   ├── anomaly/           # Anomaly detection engines| `POST /api/chat/multimodal` | Chat with optional `audio`/`image`/`video`; returns `meta.attachments` (voice/vision/face/STT). |

│   ├── mlops/             # MLOps utilities

│   └── train/             # Training scripts```bash| `GET /api/chat/stream?message=...` | SSE streaming; uses OpenAI when `OPENAI_API_KEY` is set, otherwise streams the offline reply. |

├── models/                 # Trained model artifacts

├── data/                   # Datasets & embeddings# Manual deployment| `POST /api/rag/query` | Retrieve passages from local docs (vector-store if available, TF-IDF fallback). |

├── benchmarks/             # Evaluation suite

├── docs/                   # Documentationcd ui-web/frontend| `POST /api/rag/ingest` / `POST /api/rag/upload` | Add docs to `data/docs/` and rebuild the local RAG index. |

└── tests/                  # Test suite

```npm run build| `POST /api/risk/analyze` | Risk “command center” scoring + decision + optional explanation + monitoring log. |



## 📚 Documentationnpm run deploy| `GET /api/monitor/summary` / `GET /api/monitor/drift` | Monitoring summaries + drift report (JSONL logs under `data/monitoring/logs/`). |



| Document | Description |```| `POST /api/recommend` | Recommendations (items) + MovieLens-style scoring + numeric-vector fallback. |

|----------|-------------|

| [Architecture](docs/ARCHITECTURE.md) | System architecture & design || `POST /api/recommend/multimodal` | Multimodal similarity (image/text). Falls back to an offline index on macOS if FAISS isn’t available. |

| [MLOps Roadmap](docs/MLOPS_ROADMAP.md) | Shadow mode & deployment |

| [API Notes](docs/api_streamlit_notes.md) | API implementation details |## License| `POST /api/voice/emotion` | Voice emotion label + confidence from an uploaded audio file. |

| [Production Deploy](docs/PRODUCTION_DEPLOYMENT.md) | Deployment checklist |

| [Legacy Code](docs/LEGACY.md) | Legacy module documentation || `POST /api/stt/transcribe` | Speech-to-text (requires `faster-whisper`). |



## 🛠️ Technology StackMIT License - see [LICENSE](LICENSE)| `POST /api/vision/predict` | Image classification (requires trained ResNet artifact). |



- **Backend**: FastAPI, Python 3.11, Pydantic| `POST /api/vision/face_emotion/predict` | 7-class facial emotion (requires trained artifact). |

- **Frontend**: React 18, TypeScript, Tailwind CSS, Vite

- **ML**: scikit-learn, PyTorch, XGBoost, LightGBM---| `POST /api/vision/video/predict` | Video inference via sampled frames + temporal heuristics (requires `ffmpeg`). |

- **Vision**: YOLO, OpenCV, Pillow

- **Voice**: Whisper, librosa| `POST /api/vision/brand/predict` | YOLO logo/brand detector (requires `artifacts/brand/yolo_logo_det.pt`). |

- **MLOps**: MLflow, DVC, Prometheus

- **Infrastructure**: Docker, GitHub Actions**Developed for CIS 380** | University Project| `GET /health` / `GET /health/detailed` / `GET /metrics` | Production health/readiness + Prometheus metrics. |



## 📈 Data

## Training (Practical)

| Dataset | Size | Domain |

|---------|------|--------|Canonical entrypoints:

| UNSW-NB15 | ~2GB | Cybersecurity |- `python scripts/train_all.py` (fraud/cyber/behavior/fusion + voice + recommender)

| MovieLens | ~500MB | Recommendations |- `python scripts/train_all.py --with-brand` (brand/logo YOLO smoke-run by default; override env vars for full training)

| CelebDF | ~66GB | Vision/Deepfake |- `python scripts/train_all.py --with-face-emotion` (7-class face emotion)

| Custom Fraud | ~100MB | Financial |- `python scripts/train_all_vision.py` (vision wrapper; can be heavy depending on datasets)



## 🤝 ContributingBrand/logo YOLO (full control via env vars):

- Prepare dataset: `python scripts/prepare_brand_data.py`

1. Fork the repository- Train: `python -m src.train.train_brand_logo_detector`

2. Create a feature branch (`git checkout -b feature/amazing-feature`)- Tip for macOS: validation can be slow; set `BRAND_VAL=false` and/or `BRAND_VAL_MAX_IMAGES=2000`.

3. Commit changes (`git commit -m 'Add amazing feature'`)

4. Push to branch (`git push origin feature/amazing-feature`)See `scripts/README.md` for the complete list.

5. Open a Pull Request

## Testing / Quality

## 📄 License```bash

pytest -q

MIT License - see [LICENSE](LICENSE)ruff check app tests

```

---

The CI workflow (`.github/workflows/ci.yml`) runs lint + a focused test set and builds the Docker image.

**Developed for CIS 380** | University of Pennsylvania

## Documentation
Start here: `docs/README.md`

## License
MIT (see `LICENSE`).
