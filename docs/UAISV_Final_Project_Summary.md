# UAIS‑V2 (OmniChatX) — Project Summary

This repository implements **OmniChatX / Universal Anomaly Intelligence v2**: a multimodal AI agent platform that routes user requests to specialized subsystems (RAG, risk scoring, recommendations, voice emotion, vision) and returns a unified response.

## 1) What the System Does

OmniChatX exposes a single “chat” surface (`/api/chat`) and a Streamlit UI that can:
- answer questions using a **local document knowledge base** (RAG),
- compute a **risk decision** from a simple “command center” payload (fraud/cyber/behavior + fused risk),
- generate **recommendations** (text + multimodal similarity),
- analyze **audio** for emotion (and optionally speech-to-text),
- analyze **images/videos** (image classification, video frame sampling, face emotion, and a YOLO logo detector).

The system is designed to be usable **offline**: if `OPENAI_API_KEY` is not set, the orchestrator falls back to local behaviors and local RAG. Online LLM support is additive, not required.

## 2) Key Features (Engineering)
- **Unified routing:** one request → one chosen route → structured response (`route`, `answer`, `meta`).
- **Multimodal handling:** optional `audio`/`image`/`video` uploads with results attached under `meta.attachments`.
- **Observability:** production health checks (`/health/*`) and Prometheus metrics (`/metrics`).
- **Reproducible scripts:** single-command trainers and deterministic “smoke runs” to validate the setup.
- **Production-style deployment:** Docker Compose stack (API + UI + Redis + optional monitoring/nginx).

## 3) Architecture Overview

```text
Streamlit UI  --->  FastAPI gateway  --->  Orchestrator  --->  Modules
                         |                 (routing)         (RAG, risk, recs, voice, vision)
                         |
                         +--> monitoring logs + metrics
```

Canonical entrypoints:
- API: `app/main.py` → `backend/main.py`
- UI: `app/streamlit_chatbot/app.py`

## 4) How to Run (Local)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload
OMNICHATX_BACKEND=http://localhost:8000 streamlit run app/streamlit_chatbot/app.py
```

One-command demo:
```bash
bash scripts/run_demo.sh
```

## 5) Training & Artifacts (Optional)

The repo works even without trained artifacts, but some endpoints will return `503` until the corresponding model is trained.

Common entrypoints:
- `python scripts/train_all.py` (core)
- `python scripts/train_all.py --with-face-emotion`
- `python scripts/train_all.py --with-brand`

Brand/logo YOLO:
- Prepare: `python scripts/prepare_brand_data.py`
- Train: `python -m src.train.train_brand_logo_detector`

## 6) Deployment (Docker)

Use the production compose stack:
```bash
cp .env.production.example .env
docker compose -f docker-compose.production.yml up -d --build
```

See `docs/PRODUCTION_DEPLOYMENT.md` for details and optional profiles (monitoring/nginx).

