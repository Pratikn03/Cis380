# OmniChatX / Universal Anomaly Intelligence v2

## Section 1 — Project Identity
OmniChatX / Universal Anomaly Intelligence v2 is a multimodal AI agent platform driven by an orchestrator that routes incoming conversations to LLM-based chat, RAG, fraud/cyber/anomaly scoring, speech emotion recognition, and explainable recommendation services. The system ships with monitoring and drift-detection tooling, a Streamlit demo UI, and a CI/CD-backed Docker deployment so that the entire stack can be iterated like a production service.

## Section 2 — High-Level Architecture
* **FastAPI backend (`app/`)** exposes a single API gateway (`app/main.py`) that mounts routers for chat, RAG ingestion, risk scoring, recommendation, voice, monitoring, and health checks.
* **AI agent orchestrator (`app/agent/`)** runs the `OmniChatXOrchestrator` decision engine, keeps lightweight user memories, and fuses router outputs, citations, and metadata before returning a response.
* **Modular AI services** live under `app/api/`, `app/rag/`, `app/models/`, and `app/monitoring/`—each module (RAG retriever, fraud/cyber/behavior APIs, voice emotion predictor, explainable recommender, monitoring logger/drift) can be swapped or extended independently.
* **Streamlit UI and static frontend** (`app/streamlit_chatbot`, `ui/`) consume the orchestrator APIs to showcase chat, recommendation, risk overlays, and embeddings-driven RAG demos.
* **Docker + CI/CD** (`Dockerfile`, `docker-compose.yml`, `.github/workflows/ci.yml`) package the stack, run lint/tests, and build the production image as part of the pipeline.

**Request lifecycle:** user → FastAPI ingress → orchestrator decision engine → selected module (RAG, fraud/cyber/anomaly, recommender, voice, fallback chat) → module prediction + monitoring/logging → orchestrator aggregates answer + lineage → response returned. This agent-based routing keeps the stack flexible while tracing each step for observability.

## Section 3 — Core Features (What Is Implemented)
1. **AI Agent Orchestrator** (`app/agent/orchestrator.py`) routes intent via a decision engine, consults the `LLMStub`, executes module-specific helpers, tracks user memory, and annotates answers with citations or risk notes.
2. **Retrieval-Augmented Generation** (`app/rag/ingest.py`, `app/rag/retriever.py`, `app/rag/prompting.py`) ingests `docs/` content, builds TF-IDF embeddings, retrieves relevant chunks, and supplies `citations` to the orchestrator for transparent responses.
3. **Fraud / Cyber / Behavior Anomaly APIs** (`app/api/fraud.py`, `app/api/monitor.py` plus legacy `backend/api/*`) surface scoring from `models/fraud/`, `models/cyber/`, and `models/behavior/` artifacts, logging each invocation.
4. **Fraud Monitoring & Drift Detection** (`app/monitoring/`) append events to `data/monitoring/logs/fraud_events.jsonl`, compute freshness summaries, and expose summary/drift reports via `/api/monitor/summary` and `/api/monitor/drift`.
5. **Speech Emotion Recognition** (`app/models/voice/emotion_predict.py`, `app/api/voice.py`) extracts MFCC features, loads a fallback classifier, and delivers emotion/confidence once users upload audio.
6. **Explainable Recommendation Engine** (`app/models/recommender/` and `recommender/` packages) powers `/api/recommend` and `/api/recommend/explain`, supporting movie-style metadata, vectorized fallbacks, and text explanations.
7. **Streamlit Demo UI** (`app/streamlit_chatbot/app.py`) wires chat, fraud risk, and recommendation tabs to the orchestrator (`app/agent`), styling the experience, showing tags, and surfacing risk overlays.
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
- `data/` — document corpus, embeddings, monitoring logs, and other persistent artifacts ingested by RAG and monitoring layers.
- `tests/` — pytest suites that validate chat routing, RAG retrieval, and monitoring/drift tooling.
- `docs/` — architecture diagrams, component walkthroughs, and demos used to explain the architecture.

> Legacy or experimental directories such as `backend/`, `agent/`, `api/`, `rag/`, `recommender/`, `scripts/`, `experiments/`, and `deploy/` remain in the tree for reference, but `app/` is the active runtime in new deployments.

## Section 5 — How to Run (Local)
1. Create and activate a Python 3.11 virtual environment.
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Start the FastAPI backend.
   ```bash
   uvicorn app.main:app --reload
   ```
3. Launch the Streamlit UI, pointing at the running backend if it is not on `http://localhost:8000`.
   ```bash
   OMNICHATX_BACKEND=http://localhost:8000 streamlit run app/streamlit_chatbot/app.py
   ```
4. Run the pytest suites that cover chat, RAG, and monitoring logic.
   ```bash
   pytest tests/test_chat.py tests/test_rag.py tests/test_monitoring.py -q
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
| `POST /api/chat` | Ingests text (and optional audio/attachments), routes via the orchestrator, and returns routed answers plus metadata/citations. |
| `POST /api/rag/ingest` | Appends or updates document content under `docs/`, triggers the TF-IDF ingestion pipeline, and reports the number of indexed chunks. |
| `POST /api/voice/emotion` | Accepts audio uploads, extracts MFCC features, and returns an emotion label with confidence from the fallback classifier. |
| `POST /api/recommend` | Predicts recommendations via explainable XGBoost-based pipelines and MovieLens-derived metadata depending on the payload. |
| `POST /api/recommend/explain` | Returns short, feature-driven explanations for a user/item pair by calling `app/models/recommender/explain.py`. |
| `GET /api/monitor/summary` | Summarizes the latest fraud log metrics, request counts, and recent risk scores recorded in `data/monitoring/logs`. |
| `GET /api/monitor/drift` | Computes drift summaries against the stored baseline (`app/monitoring/baseline.py`) and exposes feature-level deltas. |
| `GET /health` | Lightweight uptime/status ping (also used by the Docker healthcheck). |

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
* RAG pipeline currently uses local TF-IDF embeddings; replacing it with a managed vector DB (Chroma/Pinecone) is a logical next step.
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
