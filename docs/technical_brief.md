# SentinelForge Technical Brief

SentinelForge is a multimodal AI agent platform that integrates multiple “applied AI” subsystems behind a single API and demo UI:
- retrieval over local documents (RAG),
- risk scoring (fraud/cyber/behavior + a fused decision),
- recommendations (text + multimodal similarity),
- voice emotion recognition (audio),
- vision inference (image/video) + optional face emotion + brand/logo YOLO.

## Design Goals
- **One interface, many tools:** one request surface with routing + unified responses.
- **Offline-first:** everything runs locally without external services; optional online LLM is additive.
- **Production-minded:** clear entrypoints, health checks, metrics, and a Docker production stack.

## High-Level Architecture

Components:
- **API Gateway:** `app/main.py`
- **Routing layer:** rule-based orchestrator (default) under `app/agent/` (legacy kept under `app/legacy/agent/`)
- **Services:** modular code under `app/` (risk, monitoring, voice, RAG ingestion, brand, STT, health)
- **UI:** Streamlit command center under `app/streamlit_chatbot/`
- **Artifacts:** local models under `models/` and `artifacts/` (not committed)

## Runtime Behavior
- `/api/chat` routes text to the relevant subsystem and returns `{route, answer, meta}`.
- `/api/chat/multimodal` accepts optional `audio`/`image`/`video` and attaches analysis outputs under `meta.attachments`.
- Health and observability are provided via `/health/*` and `/metrics`.

## Deployment
- Dev: `uvicorn app.main:app --reload` + `streamlit run app/streamlit_chatbot/app.py`
- Production: `docker-compose.production.yml` (API + UI + Redis + optional monitoring/nginx)

## Known Constraints
- Some features require trained local artifacts and will return `503` until trained.
- On macOS (Apple Silicon), PyTorch uses `mps` (Metal). Validation in YOLO may be slower; disabling validation for smoke runs is recommended.
