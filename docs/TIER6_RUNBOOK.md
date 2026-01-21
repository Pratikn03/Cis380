# Tier-6 Operations Runbook

## Services

- `api`: FastAPI gateway on :8000
- `worker`: Celery worker for async jobs
- `postgres`: metadata store for jobs/runs/audit logs
- `redis`: queue + cache
- `mlflow`: tracking server on :5000
- `next`: product UI on :3000

## Common tasks

```bash
# Start full stack
Docker compose -f docker-compose.elite.yml up --build

# Create admin user (first run)
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=changeme

# Trigger RAG indexing
curl -X POST http://localhost:8000/api/v1/rag/index

# Check jobs
curl http://localhost:8000/api/v1/jobs?limit=5
```

## Observability

- `/metrics` for Prometheus
- `logs/` for API + job logs
- `reports/` for evaluation outputs
