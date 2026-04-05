# Reproducibility (Tier-6)

## Local (full stack)

```bash
# Start full stack
Docker compose -f docker-compose.elite.yml up --build
```

## Backend only

```bash
uvicorn app.main:app --reload --port 8000
```

## Run migrations (SQLite/Postgres)

```bash
alembic upgrade head
```

## Build RAG index

```bash
curl -X POST http://localhost:8000/api/v1/rag/index
```

## Run tests

```bash
pytest -q
```
