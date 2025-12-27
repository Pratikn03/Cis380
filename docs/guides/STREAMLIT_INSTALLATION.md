# Streamlit UI Setup (SentinelForge)

This guide covers running the Streamlit UI against the FastAPI backend.

## Prerequisites
- Python 3.11+ recommended
- Dependencies installed: `pip install -r requirements.txt`

## Start the Backend

```bash
uvicorn app.main:app --reload --port 8000
```

Health check:
```bash
curl http://localhost:8000/health
```

## Start the Streamlit UI

```bash
export SENTINELFORGE_BACKEND="http://localhost:8000"
streamlit run app/streamlit_chatbot/app.py
```

## Optional: Enable Authentication

If you set `AUTH_TOKEN`, the backend will require a bearer token on `/api/*` routes.

```bash
export AUTH_TOKEN="your-token"
uvicorn app.main:app --reload --port 8000
```

The Streamlit UI reads `AUTH_TOKEN` and sends it automatically.

## Optional: WebRTC (Live Mic/Camera)

Some “live” UI features use `streamlit-webrtc`. If you want it:

```bash
pip install -r requirements-optional.txt
```

## Next
- UI walkthrough: `docs/unified_chat_guide.md`
- 5-minute demo script: `docs/guides/demo.md`
