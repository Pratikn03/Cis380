# Legacy Modules (Read-only reference)

These folders are retained for historical context, experimentation, or documentation purposes. The actively maintained production system lives under `app/`.

## Legacy components

- `agent/` — Original orchestrator, policy, and SHAP utilities before the `app.agent` rewrite.
- `rag/` — Older TF-IDF retriever, vector store helpers, and service that powered local document search prior to `app.rag`.
- `api/routes/` — Legacy FastAPI routes (chat, rag, recommend, fraud, cyber, behavior, vision) before the new `app/api` package.
- `recommender/` — Research recommender experiments (LightFM, NCF, hybrid ranking) kept for reference and model artifacts.
- `src/uais/` — Research-oriented fusion, drift, NLP, and vision pipelines (UAIS core codebase) retained for insights and prototypes.

These modules are retained for historical reference and experimentation. The actively maintained production stack lives under `app/`.
