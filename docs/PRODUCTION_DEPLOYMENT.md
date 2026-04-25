# Production Deployment Runbook

## Purpose
Define the canonical Docker VM production deployment path for Sentifargo services, quality checks, and rollback operations.

## Scope
- API, worker, Kotlin GraphQL gateway, Next command center, Nginx, Postgres, Redis, Prometheus, Grafana, and Redis exporter via `docker-compose.production.yml`
- Environment setup from `.env.production.example`
- Post-deploy health validation
- Rollback and incident-safe recovery steps

## Prerequisites
1. Docker and Docker Compose are installed and working.
2. Required files are present:
   1. `Dockerfile.production`
   2. `ui-web/next/Dockerfile`
   3. `services/gateway-kotlin/Dockerfile`
   4. `docker-compose.production.yml`
   5. `scripts/deploy.sh`
   6. `artifacts/release/model-manifest.json`
3. Production environment file exists:
   1. `cp .env.production.example .env`
4. `.env` is populated with production-safe values:
   1. `SECRET_KEY`
   2. `DATABASE_URL`
   3. `REDIS_URL`
   4. `CORS_ORIGINS`
   5. `ALLOWED_HOSTS`
   6. `FORCE_HTTPS=true`
   7. `MODEL_MANIFEST_PATH=artifacts/release/model-manifest.json`
   8. `GRAFANA_PASSWORD`
   9. `OPENAI_API_KEY` (if OpenAI-backed features are enabled)

## Pre-deploy validation
Run from repository root:

```bash
make quality-docs-fast
make quality-fast
make quality-data
python scripts/check_production.py
python scripts/artifact_gate.py
python scripts/model_quality_gate.py
docker compose -f docker-compose.production.yml config
```

`scripts/model_quality_gate.py` is release-blocking. If any domain fails its strict threshold or smoke inference evidence is missing, do not deploy.

## Deploy
1. Default deployment:

```bash
bash scripts/deploy.sh deploy
```

2. Direct Compose deployment:

```bash
docker compose -f docker-compose.production.yml up -d --build
```

## Post-deploy smoke checks
1. Service status:

```bash
bash scripts/deploy.sh status
```

2. API readiness:

```bash
curl https://your-domain.com/health/ready
```

3. If gateway is deployed separately, verify:

```bash
curl http://localhost:8081/actuator/health
```

4. For a detailed dependency snapshot, run:

```bash
curl -H "Authorization: Bearer $AUTH_TOKEN" https://your-domain.com/health/detailed
```

The readiness endpoint must report healthy database, Redis, Celery worker, disk, memory, and release model manifest components before the stack is considered live.

## Rollback
1. Stop current stack:

```bash
bash scripts/deploy.sh stop
```

2. Restart previous known-good image/tag (if pinned in your deployment environment).
3. Restore backups if required:

```bash
bash scripts/deploy.sh restore
```

## Ownership and canonical links
- Owner: Sentifargo Platform Team
- Last verified: 2026-04-25
- Canonical docs index: `README.md`
- Canonical map: `CANONICAL.md`
