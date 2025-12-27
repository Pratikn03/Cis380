# Architecture

This project is organized as a single FastAPI “gateway” plus modular AI subsystems and a Streamlit demo UI.

## Data Flow (High Level)

```mermaid
flowchart TD
    UI[Streamlit UI] --> API[FastAPI Gateway]
    API --> ORCH[Orchestrator]

    ORCH --> CHAT[Chat (offline-first, OpenAI optional)]
    ORCH --> RAG[RAG (data/docs + embeddings)]
    ORCH --> ML[Risk + Recs + Voice + Vision]

    API --> MON[Monitoring + Metrics]
    ML --> MON
```

## Key Entry Points
- FastAPI: `app/main.py`
- Streamlit UI: `app/streamlit_chatbot/app.py`

## Notes on “Legacy”
The gateway intentionally mounts both:
- `api/routes/*` (legacy endpoints that are still used by the Streamlit UI), and
- selected `app/api/*` routers (risk/monitor/voice/rag ingestion/brand/stt/health).

See `docs/LEGACY.md` for details.
