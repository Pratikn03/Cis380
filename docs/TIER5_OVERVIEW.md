# Sentifargo Tier-5 Overview

Sentifargo is a Tier-5, production-style multimodal risk + intelligence platform that looks and behaves like a real service (not a notebook demo). Its purpose is to accept a single user request (text, image, audio, document) and route it to the correct intelligence engine (fraud, cyber, behavior, fusion risk, RAG/QA, recommendations, voice emotion, vision/brand recognition, and an offline-first DSA RAG). The system returns a single structured response with an answer plus evidence/metadata so results can be trusted, monitored, and improved over time.

## 1) Core idea and why this exists

Most student projects prove one model works. Sentifargo proves you can build a full AI platform: APIs, UI, training, monitoring, and reproducible execution. The main product is an orchestrated platform that can:

- Detect anomalies and risk (fraud/cyber/behavior) from tabular or event data.
- Explain decisions (why a transaction looks suspicious, why a session is anomalous, why a prediction was made).
- Support multimodal analysis (image/video authenticity, logo/brand detection, voice emotion cues).
- Answer knowledge questions grounded in documents (general RAG + a dedicated DSA RAG).
- Recommend content/items (MovieLens and multimodal similarity/retrieval style recommendations).
- Operate offline-first while allowing an optional online/LLM fallback when enabled.

The elite part is not only the models. It is that the platform is designed for correctness, transparency, deployment readiness, and governance.

## 2) Platform architecture (how everything fits together)

### Entry points
- FastAPI API gateway (app/main.py) is the primary service interface.
- Streamlit Command Center (app/streamlit_chatbot/app.py) is the operational UI for humans (demo + dashboards).
- Optional deploy API (deploy/api/main.py) provides a minimal prediction surface for deployment demos.

### Layered system design
1. Interfaces
   - React UI (web) + Streamlit UI (command center)
   - REST/JSON endpoints for programmatic use
2. Orchestration
   - A router/orchestrator decides what subsystem should handle the request.
   - It outputs: {"route": "...", "answer": "...", "meta": {...}} so every response has structure.
3. Intelligence engines
   - Fraud engine (tabular transaction scoring)
   - Cyber engine (network/session anomalies + event/timeline support)
   - Behavior engine (user activity/insider risk patterns)
   - Fusion risk engine (combines signals into one risk decision)
   - Recommender engine (MovieLens + multimodal recommend)
   - Vision engine (image/video analysis + deepfake/auth checks)
   - Brand/logo engine (YOLO/Ultralytics style detection)
   - Voice engine (emotion / stress / speech signals)
   - RAG engines: general document QA + DSA-focused RAG
4. Data + artifacts
   - Datasets under data/ with raw/interim/processed organization
   - Embeddings and indexes for RAG under data/docs, data/embeddings, plus DSA-specific stores
   - Trained model artifacts loaded at runtime (joblib/torch loads)
5. Ops / MLOps
   - Docker and Compose for reproducible runtime
   - CI workflows for testing/build gates
   - Prometheus metrics endpoint for monitoring
   - MLflow/DVC patterns + roadmap for registry/versioning/shadow deployments

## 3) Major features (what a user can do)

### A) Fraud detection (tabular risk scoring)
- Risk score / class (normal vs suspicious).
- Explanation metadata (feature importance or explanation hooks).
- Response suitable for UI cards and monitoring logs.

### B) Cyber threat analytics + timeline views
- Event summaries (/events, /summary).
- Pattern extraction (/patterns, /sources).
- Anomaly scoring logic (Isolation Forest / sequence models).

### C) Behavior analytics (insider-style anomaly signals)
- Session behavior logs ingestion.
- Anomaly scoring (statistical / ML).
- Reporting into monitoring logs for drift/audit analysis.

### D) Fusion risk engine (one decision from many signals)
- Combines outputs from fraud/cyber/behavior/vision/voice.
- Produces a unified risk summary suitable for dashboards.
- Supports rules + meta-model strategies.

### E) Recommendations (MovieLens + multimodal)
- Personalized top-k recommendations.
- Optional explanation endpoint.
- Multimodal recommendation (image/text similarity).
- Local offline catalogs for clothes, cars, and places (data/catalogs/*.jsonl).

### F) Vision intelligence (image/video analysis)
- Image classification pipelines.
- Video temporal inference (frame sampling or temporal model).
- Face emotion model (if present).
- Deepfake/auth detection datasets integrated into training scripts.

### G) Brand/logo recognition (YOLO/Ultralytics)
- Detect brand/logo from uploaded image.
- Return bounding boxes + confidence.
- Can be linked to recommendation outputs (brand -> product suggestions).
- Supports multiple model kinds (logo/car/fashion) when trained; select via `kind` on `/api/vision/brand/predict`.

### H) Voice intelligence (emotion / speech signals)
- Estimate emotion or stress cues.
- Optional STT transcription endpoint.
- Voice signals can be integrated into fusion risk.

### I) RAG: Document QA (general)
- Document ingestion/upload.
- Embedding creation and storage.
- Query-time retrieval and grounded answers.

### J) DSA RAG (offline-first + optional online fallback)
- Rewrite -> retrieve (dense + BM25) -> merge/dedupe -> rerank -> answer + citations.
- Offline-first: works with local embeddings/BM25 + stored DSA docs.
- Online fallback (optional) when confidence is low.
- Scope is focused for high-quality retrieval (Arrays, Search/Sort, Linked Lists, Stack/Queue).

## 4) Training and reproducibility (what makes it not a demo)

The repo includes training entrypoints (scripts/train_all.py, src/train/*) and a clean data layout under data/. Tier-5 maturity comes from:
- Model training scripts exist.
- Runtime model loading exists.
- APIs wrap models cleanly.
- UI can drive the system end-to-end.

## 5) Monitoring + operational visibility

- Prometheus-style metrics and monitoring endpoints.
- JSONL logs for drift summaries and audit trails.
- Streamlit dashboards for metrics and health.

## 6) Legacy compatibility (current vs legacy)

- Current API lives under app/api/*.
- Legacy endpoints under app/legacy/api/routes/* remain for compatibility/testing.
- Tier-6 direction is to make current vs legacy explicit and enforce a canonical contract.

## 7) Final identity (single product view)

Sentifargo is a unified risk + intelligence command center that ingests multimodal signals (transactions, logs, text, docs, images, audio) and produces grounded, explainable decisions and recommendations through a production-style API + UI, with offline-first RAG and measurable monitoring.

A user should be able to:
1. Open the UI and run a chat-like request (analyze risk, recommend, check image/logo, transcribe audio, ask DSA question).
2. The orchestrator routes to the correct module.
3. The response includes: answer, confidence/score, citations/context, and explanation metadata.
4. The system logs the event and exposes metrics for monitoring.

## 8) Tier-6 direction (0.5 percent elite upgrade path)

To reach Tier-6, add:
- Contract gate: UI endpoints must match OpenAPI (no drift).
- System scorecard: one command generates latency/status report across modules.
- E2E smoke tests: CI proves core endpoints run.
- Artifact governance: missing models fail loudly with clear errors.
- Shadow mode: model updates are safe and measurable.
