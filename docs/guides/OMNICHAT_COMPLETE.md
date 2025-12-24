# OmniChatX Capabilities (UI Summary)

This document is a high-level feature list for the Streamlit UI and the backing API.

For the full UI guide, see `docs/omnichat_unified_guide.md`.

## Core Capabilities
- **Chat + routing** (`/api/chat`, `/api/chat/multimodal`)
- **RAG over local docs** (`data/docs`, `/api/rag/*`)
- **Risk scoring** (fraud/cyber/behavior + fused decision via `/api/risk/analyze`)
- **Recommendations** (text + multimodal similarity via `/api/recommend/*`)
- **Voice emotion** (`/api/voice/emotion`)
- **Vision**
  - image classification (`/api/vision/predict`, requires local weights)
  - video frame sampling + temporal heuristics (`/api/vision/video/predict`, requires `ffmpeg`)
  - face emotion (`/api/vision/face_emotion/predict`, requires local weights)
  - brand/logo YOLO (`/api/vision/brand/predict`, requires local weights)

## Offline vs Online
- Offline-first by default (local models + local RAG).
- Set `OPENAI_API_KEY` to enable OpenAI-backed chat behavior and streaming (`/api/chat/stream`).

