# Voice Emotion Display Fix (Historical)

This document describes a UI-side change made during development to correctly display voice emotion predictions returned by the backend.

## Root Cause
Different backend paths returned emotion data in different places (e.g., top-level fields vs. nested under `meta.voice` / `meta.attachments.voice`).

## Fix
The Streamlit UI was updated to read emotion information from multiple possible locations and render:
- the emotion label
- the confidence score (as a percentage)

## Related
- Backend voice endpoint: `POST /api/voice/emotion`
- Multimodal chat attaches voice outputs under `meta.attachments.voice`: `POST /api/chat/multimodal`

