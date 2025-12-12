# Project Status

This document tracks the definition of done for OmniChatX and records what is currently implemented vs. still outstanding.

## Definition of Done (the promise)
OmniChatX must deliver everything listed below for us to call it “done”:

1. **Text chat** via LLMs (and local fallbacks) ➜ FastAPI `/api/chat` routes through `agent/orchestrator.route` and, when configured, calls OpenAI or the local RAG service (`agent/orchestrator.py` + `rag/service.py`).
2. **Recommender endpoint** ➜ `/api/recommend` exists (`api/routes/recommend.py`) and loads joblib models from `models/recommender`.
3. **Vision tasks** ➜ `/api/vision/train` summarizes vision datasets and optionally runs the TensorFlow helper from `src/uais/vision/train_vision_model.py`.
4. **Offline capability** ➜ Fraud, cyber, and behavior scoring all use local joblib artifacts (`models/*`) and do not need external services; RAG also works over local docs.
5. **Exposed API/UI** ➜ FastAPI backend (`backend/main.py`) and multiple UIs (`app/streamlit_chatbot/app.py`, `ui/index.html`, Streamlit + static HTML).

## Master Checklist

### A. Core Functionality
- [x] Text chat `/api/chat` works (FastAPI router + orchestrator, `api/routes/chat.py:11-55`).
- [x] Recommender API is implemented (`api/routes/recommend.py:1-190`).
- [x] Vision endpoint `/api/vision/train` summarizes datasets and can run the TensorFlow vision helper (`api/routes/vision.py:1-73`).
- [x] Offline mode works for the shipped models (`agent/orchestrator.py:88-245` loads joblib artifacts).
- [x] Structured logging/metrics are available via `/metrics` (`backend/main.py:8-68` + Prometheus counters).

### B. Quality & Reliability
- [x] Input validation and model-not-found errors raise friendly `HTTPException`s (`api/routes/fraud.py:28-46`, `cyber.py`, `behavior.py`, `recommend.py`).
- [x] Model failures are caught and translated into HTTP errors (`try/except` blocks throughout `api/routes/*`).
- [x] Tests pass locally (`pytest` now completes with 6 passes and 2 skips; TensorFlow/HuggingFace-heavy tests run only when `RUN_TF_TESTS=1`).
- [ ] No unhandled exceptions cannot be guaranteed until additional coverage arrives.

### C. Developer Experience
- [x] README documents the system overview and features (`README.md:7-200`).
- [x] Installation steps and dependencies are spelled out (`README.md:80-130`, `requirements.txt`, `requirements-optional.txt`, `pyproject.toml`).
- [x] Run instructions for backend/UI are listed in README and `scripts/start_all.sh`.
- [x] Sample API endpoints are listed (`README.md:118-140`).
- [x] Folder layout is documented (`README.md:139-200`).

### D. User Experience
- [x] Streamlit chatbot + static UI exist (`app/streamlit_chatbot/app.py`, `ui/index.html`, `ui/styles.css`, `app/chatbot` components).
- [x] Fraud/Cyber/Behavior panels now visible via the Streamlit “Risk & Anomaly” tab (forms hitting `/api/fraud`, `/api/cyber`, `/api/behavior`).
- [x] Demo script (`docs/demo.md`) documents the five-minute tour that covers recommendation, fraud, RAG, vision, and metrics.
- [x] Errors use `HTTPException` codes with explanatory text when models are absent.

### E. Cleanliness
- [ ] TODO/FIXME markers remain in critical modules (`rg TODO` identifies `rag/*`, `app/chatbot/context_manager.py`, `src/train/*.py`, `src/uais/*`, etc.).
- [x] Dependency files are maintained (`requirements.txt`, `requirements-optional.txt`, `pyproject.toml`).
- [x] Dead/experimental artifacts (`scripts/*.sh`, notebooks) are documented (`docs/experimental_assets.md`).

## Summary

Core APIs, orchestrator, offline scoring modules, the `/api/vision/train` helper, the RAG loader/embed/retriever pipeline, the fraud/cyber models, the experimental assets documentation, and the five-minute demo instructions are solid, and the `pytest` suite now finishes (6 passes, 2 skips when `RUN_TF_TESTS` is unset). The recommender now includes electronics, courses, budget decision support, and the risk-aware overlay, while context memory keeps preferences for future queries—only the remaining TODO markers remain before a final ship.

## Next steps

1. Provide a quick-start demo script or guide (“OmniChatX in 5 minutes”) for the UI/API surface.
