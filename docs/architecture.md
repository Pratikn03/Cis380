```mermaid
flowchart TD
    UI[UAIS-V UI<br/>(Streamlit Command Center)]
    API[FastAPI Gateway<br/>(app.main:app)]
    ORCH[Agent Orchestrator<br/>(rule-based routing)]

    UI --> API
    API --> ORCH

    ORCH --> CHAT[Chat / LLM<br/>(OpenAI optional, offline fallback)]
    ORCH --> RAG[Local RAG<br/>(docs + TF-IDF / local embeddings)]
    ORCH --> ML[ML Modules<br/>(Fraud • Cyber • Behavior • Recsys • Voice • Vision)]

    API --> MON[Monitoring Logger<br/>(JSONL events)]
    ML --> MON

    MON --> SUM[/api/monitor/summary<br/>/api/monitor/drift/]
```

**Legend:**
- **UAIS-V UI**: Streamlit demo UI (`app/streamlit_chatbot/app.py`)
- **FastAPI Gateway**: canonical server entrypoint (`app/main.py` → `backend/main.py`)
- **Agent Orchestrator**: routes requests to the right module (chat/RAG/risk/recs/voice/vision)
- **Local RAG**: document-grounded answers from local files (`data/docs/`, `data/embeddings/`)
- **ML Modules**: fraud/cyber/behavior/recommender/voice/vision inference endpoints
- **Monitoring Logger**: writes events under `data/monitoring/logs/*.jsonl` and summarizes them via `/api/monitor/*`
