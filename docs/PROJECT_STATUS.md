# Project Status

This file is a lightweight status snapshot (high level, no guarantees). For how to run the demo, see `README.md` and `docs/guides/demo.md`.

## Current (Works End-to-End)
- FastAPI gateway (`app/main.py`) with auth + CORS + health + metrics
- Streamlit UI (`app/streamlit_chatbot/app.py`)
- Orchestrated chat (`/api/chat`, `/api/chat/multimodal`)
- Local RAG (ingest/query) and offline fallback behavior
- Risk “command center” + monitoring/drift summaries
- Recommender (text + multimodal; offline fallback index on macOS)

## Optional (Requires Local Artifacts / Extras)
- Brand/logo YOLO detector (`artifacts/brand/yolo_logo_det.pt`)
- Face emotion classifier (`models/vision/face_emotion/model.pt`)
- Image/video vision classifier (`models/vision/resnet/model.pt`, `ffmpeg` for video)
- Speech-to-text (`faster-whisper`)
- Prometheus/Grafana + nginx (Docker Compose profiles)

## Cleanup / Future
- Consolidate legacy and newer routers into a single API surface (see `docs/LEGACY.md`)
- Add deployment hardening (rate limits, request size limits, secrets management)
