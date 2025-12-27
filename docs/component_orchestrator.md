# Orchestrator (Routing Layer)

SentinelForge is structured around an “orchestrator”: a component that decides which subsystem should answer a given request and returns one unified response.

## What It Does
- **Classifies intent** (chat vs RAG vs fraud/cyber/behavior vs recommendations).
- **Runs the selected module** (local ML, local RAG, optional OpenAI LLM).
- **Returns a structured payload** for the UI and for debugging:
  - `route`: which module handled the request
  - `answer`: the user-facing answer
  - `meta`: per-route details (scores, citations, attachments, etc.)

## Where It Lives (Current Runtime)

The chat endpoints (`/api/chat`, `/api/chat/multimodal`) use the legacy orchestrator:
- `agent/orchestrator.py` — request handling + model loading + offline/online response logic
- `agent/policy.py` — rule-based routing decisions
- `rag/service.py` — TF‑IDF RAG fallback (used when vector-store RAG isn’t available)

## Offline vs Online
- If `OPENAI_API_KEY` is **unset**, chat responses use an **offline helper** plus local RAG.
- If `OPENAI_API_KEY` is **set**, general chat routes may call OpenAI (see `agent/orchestrator.py`).

Streaming chat (`/api/chat/stream`) uses OpenAI when configured, otherwise streams the offline response.

## Multimodal Requests

`POST /api/chat/multimodal` accepts optional `audio`, `image`, and `video` uploads and attaches analysis results under:
- `meta.attachments.voice` (voice emotion)
- `meta.attachments.stt` (speech-to-text, if enabled and available)
- `meta.attachments.vision_*` (image/video summaries)
- `meta.attachments.face_emotion` (if the face-emotion model is trained)

## Next Steps (Optional Refactor)
There is also a newer orchestrator under `app/agent/*` designed for a cleaner, fully modular `app/` runtime. It is not the default chat path today (see `docs/LEGACY.md`).

