# Legacy Modules (Why They Exist)

This repository contains both “current” modules and older (but still runnable) code paths.

The goal is to keep the demo working end-to-end while migrating toward a cleaner single-stack layout.

## Canonical Runtime Today

- FastAPI entrypoint: `app/main.py` (re-exports `backend/main.py`)
- Streamlit entrypoint: `app/streamlit_chatbot/app.py`

The FastAPI gateway (`backend/main.py`) mounts:
- legacy routers under `api/routes/*` (chat, rag query, recommend, fraud, cyber, behavior, vision), and
- selected “newer” routers under `app/api/*` (risk, monitor, voice, rag ingest/upload, brand/logo YOLO, STT, vision-temporal),
- production health + metrics router from `app/core/health.py`.

## “Legacy” Directories

These are kept for reference and compatibility:
- `agent/` — legacy orchestrator used by `/api/chat` (rule-based routing; offline fallback if `OPENAI_API_KEY` is unset).
- `api/` — legacy FastAPI routers (`api/routes/*`) that the gateway still mounts.
- `rag/` — lightweight TF‑IDF RAG used as a fallback.
- `recommender/` — older recommender experiments and artifacts kept for comparison.
- `deploy/` + `dashboard/` — older API/UI experiments referenced by historical docs.

## Migration Direction

Long-term, the intent is to converge on one primary stack under `app/` (routers + orchestrator + services) and keep the top-level legacy folders as read-only archives.

