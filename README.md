# SentinelForge# SentinelForge



**SentinelForge** is a comprehensive risk intelligence platform for fraud detection, cybersecurity monitoring, and behavioral analytics.SentinelForge is a **multimodal AI agent platform** that routes a single user request to the right subsystem (RAG, fraud/cyber/behavior scoring, recommendations, voice emotion, vision) and returns a **single structured response**: `{"route", "answer", "meta"}`.



## 🌐 Live DemoThe goal of this repository is not “a chatbot in a notebook”, but an end-to-end system that looks and feels like a service: **API, UI, training, monitoring, and a repeatable test gate**.



**[View Live Demo →](https://pratikn03.github.io/Cis380/)**## What You Get

- **FastAPI gateway** (`uvicorn app.main:app`) that mounts chat + RAG + risk + recommender + vision + monitoring endpoints.

## Features- **Streamlit command center UI** (`streamlit run app/streamlit_chatbot/app.py`) with chat, multimodal uploads, and dashboards.

- **Offline-first behavior** by default (local models + local RAG). Add `OPENAI_API_KEY` to enable LLM chat/streaming.

- **Risk Analysis** - Real-time fraud and cyber threat detection- **Training entrypoints** for core models + optional vision/YOLO/face-emotion (`scripts/train_all.py`, `src/train/*`).

- **Behavioral Monitoring** - User behavior pattern analysis- **Monitoring + drift summaries** with Prometheus metrics (`/metrics`) and JSONL event logs under `data/monitoring/logs/`.

- **Voice Analytics** - Emotion detection from audio

- **Vision Processing** - Image and video analysis for security## Architecture (At a Glance)

- **Dashboard** - Interactive command center UI

```mermaid

## Architectureflowchart TD

  UI[Streamlit UI] --> API[FastAPI Gateway]

```  API --> ORCH[Orchestrator]

┌─────────────────────────────────────────────────────────────┐  ORCH --> RAG[RAG (data/docs + embeddings)]

│                    SentinelForge Platform                    │  ORCH --> RISK[Fraud/Cyber/Behavior + Fusion Risk]

├─────────────────────────────────────────────────────────────┤  ORCH --> RECS[Recommender (text + multimodal)]

│  Frontend         │  React + TypeScript + Tailwind CSS      │  ORCH --> VOICE[Voice Emotion + STT (optional)]

├───────────────────┼─────────────────────────────────────────┤  ORCH --> VISION[Vision (image/video) + Face Emotion + Brand/Logo YOLO]

│  Backend          │  FastAPI + Python                       │  API --> MON[Monitoring + Metrics]

├───────────────────┼─────────────────────────────────────────┤```

│  Models           │  Fraud, Cyber, Behavior, Voice, Vision  │

├───────────────────┼─────────────────────────────────────────┤Key entrypoints:

│  Database         │  Vector Store + Document Index          │- **API**: `app/main.py`

└───────────────────┴─────────────────────────────────────────┘- **UI**: `app/streamlit_chatbot/app.py`

```

For legacy modules and why they still exist, see `docs/LEGACY.md`.

## Quick Start

## Quickstart (Local)

### Prerequisites

- Python 3.11+### 1) Install

- Node.js 18+Recommended: Python **3.11** (matches CI).



### Installation```bash

python3 -m venv .venv

```bashsource .venv/bin/activate

# Clone repositorypip install -r requirements.txt

git clone https://github.com/Pratikn03/Cis380.git```

cd Cis380

If you plan to use included LFS-tracked artifacts (e.g., `artifacts/brand/yolo_logo_det.pt`):

# Setup Python environment```bash

python3 -m venv .venvgit lfs install

source .venv/bin/activategit lfs pull

pip install -r requirements.txt```



# Start backend### 2) Run API

uvicorn app.main:app --reload --port 8000```bash

```uvicorn app.main:app --reload

```

### Frontend Development

### 3) Run UI

```bash```bash

cd ui-web/frontendSENTINELFORGE_BACKEND=http://localhost:8000 streamlit run app/streamlit_chatbot/app.py

npm install```

npm run devUse the left sidebar for navigation. The recommended chat view is **"✨ SentinelForge (Unified Chat)"** (legacy chat UIs are still available from the Chat page).

```

### One-command demo (backend + UI)

## API Endpoints```bash

bash scripts/run_demo.sh

| Endpoint | Description |```

|----------|-------------|

| `POST /api/risk/analyze` | Risk assessment scoring |## Docker

| `POST /api/fraud` | Fraud detection |

| `POST /api/cyber` | Cybersecurity analysis |### Dev compose (single container)

| `POST /api/behavior` | Behavioral pattern analysis |```bash

| `POST /api/voice/emotion` | Voice emotion detection |docker compose up --build

| `GET /health` | System health check |```



## Project Structure### Production compose (API + UI + Redis; optional monitoring/nginx)

```bash

```cp .env.production.example .env

├── app/                    # Backend application# edit .env (AUTH_TOKEN, CORS, ports, etc)

│   ├── api/               # API routes

│   ├── models/            # ML model interfacesdocker compose -f docker-compose.production.yml up -d --build

│   └── services/          # Business logic

├── ui-web/frontend/       # React frontend# Optional: monitoring (Prometheus/Grafana)

├── models/                # Trained model artifactsdocker compose -f docker-compose.production.yml --profile monitoring up -d

├── data/                  # Datasets and embeddings

└── docs/                  # Documentation# Optional: nginx reverse proxy (requires deploy/nginx/ssl certs)

```docker compose -f docker-compose.production.yml --profile production up -d

```

## Technology Stack

See `docs/PRODUCTION_DEPLOYMENT.md` for a full deployment checklist.

- **Frontend**: React 18, TypeScript, Tailwind CSS, Vite

- **Backend**: FastAPI, Python 3.11, Pydantic## API (Quick Reference)

- **ML**: scikit-learn, PyTorch, XGBoost

- **Infrastructure**: Docker, GitHub ActionsMost routes live under `/api/*`. If `AUTH_TOKEN` is set, send `Authorization: Bearer $AUTH_TOKEN`.



## Deployment| Endpoint | What it does |

| --- | --- |

The frontend automatically deploys to GitHub Pages on push to `main`.| `POST /api/chat` | Orchestrated chat (`message`/`text`) → `{route, answer, meta}` (+ `reply` for UI compatibility). |

| `POST /api/chat/multimodal` | Chat with optional `audio`/`image`/`video`; returns `meta.attachments` (voice/vision/face/STT). |

```bash| `GET /api/chat/stream?message=...` | SSE streaming; uses OpenAI when `OPENAI_API_KEY` is set, otherwise streams the offline reply. |

# Manual deployment| `POST /api/rag/query` | Retrieve passages from local docs (vector-store if available, TF-IDF fallback). |

cd ui-web/frontend| `POST /api/rag/ingest` / `POST /api/rag/upload` | Add docs to `data/docs/` and rebuild the local RAG index. |

npm run build| `POST /api/risk/analyze` | Risk “command center” scoring + decision + optional explanation + monitoring log. |

npm run deploy| `GET /api/monitor/summary` / `GET /api/monitor/drift` | Monitoring summaries + drift report (JSONL logs under `data/monitoring/logs/`). |

```| `POST /api/recommend` | Recommendations (items) + MovieLens-style scoring + numeric-vector fallback. |

| `POST /api/recommend/multimodal` | Multimodal similarity (image/text). Falls back to an offline index on macOS if FAISS isn’t available. |

## License| `POST /api/voice/emotion` | Voice emotion label + confidence from an uploaded audio file. |

| `POST /api/stt/transcribe` | Speech-to-text (requires `faster-whisper`). |

MIT License - see [LICENSE](LICENSE)| `POST /api/vision/predict` | Image classification (requires trained ResNet artifact). |

| `POST /api/vision/face_emotion/predict` | 7-class facial emotion (requires trained artifact). |

---| `POST /api/vision/video/predict` | Video inference via sampled frames + temporal heuristics (requires `ffmpeg`). |

| `POST /api/vision/brand/predict` | YOLO logo/brand detector (requires `artifacts/brand/yolo_logo_det.pt`). |

**Developed for CIS 380** | University Project| `GET /health` / `GET /health/detailed` / `GET /metrics` | Production health/readiness + Prometheus metrics. |


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
