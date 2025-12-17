# Legacy Modules (Read-only reference)

These folders are retained for historical context, experimentation, or documentation purposes. The actively maintained production system lives under `app/`.

## Legacy components

- `agent/` — Legacy orchestrator used by the demo gateway (`backend/main.py`) for `/api/chat` routing.
- `rag/` — Older TF-IDF retriever used by the legacy orchestrator.
- `api/routes/` — Legacy FastAPI routes (chat/rag/recommend/fraud/cyber/behavior/vision) still mounted by `backend/main.py`.
- `recommender/` — Research recommender experiments (LightFM, NCF, hybrid ranking) kept for reference and model artifacts.
- `src/uais/` — Research-oriented fusion, drift, NLP, and vision pipelines (UAIS core codebase) retained for insights and prototypes.

**Important:** The project currently runs as a **hybrid gateway**:
- Canonical entrypoint: `app/main.py` (re-exports `backend/main.py`)
- Gateway mounts both:
  - legacy `api/routes/*` (chat/recs/vision/etc.)
  - newer `app/api/*` (risk, monitor, voice, RAG ingest/query, brand, STT)

Migration goal: consolidate the legacy routes/orchestrator into `app/api/*` + `app/agent/*` so the runtime is fully `app/` without duplication.
