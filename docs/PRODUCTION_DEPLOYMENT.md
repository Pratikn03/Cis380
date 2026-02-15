# Production Deployment Runbook

## Purpose
Define the canonical production deployment path for Sentifargo services, quality checks, and rollback operations.

## Scope
- API/runtime deployment via `docker-compose.production.yml`
- Environment setup from `.env.production.example`
- Post-deploy health validation
- Rollback and incident-safe recovery steps

## Prerequisites
1. Docker and Docker Compose are installed and working.
2. Required files are present:
   1. `Dockerfile.production`
   2. `docker-compose.production.yml`
   3. `scripts/deploy.sh`
3. Production environment file exists:
   1. `cp .env.production.example .env`
4. `.env` is populated with production-safe values:
   1. `SECRET_KEY`
   2. `DATABASE_URL`
   3. `REDIS_URL`
   4. `OPENAI_API_KEY` (if OpenAI-backed features are enabled)

## Pre-deploy validation
Run from repository root:

```bash
make quality-docs-fast
make quality-fast
make quality-data
python scripts/check_production.py
docker compose -f docker-compose.production.yml config
```

## Deploy
1. Default deployment:

```bash
bash scripts/deploy.sh deploy
```

2. Production profile deployment:

```bash
bash scripts/deploy.sh deploy -p production
```

3. Monitoring profile deployment:

```bash
bash scripts/deploy.sh deploy -p monitoring
```

## Post-deploy smoke checks
1. Service status:

```bash
bash scripts/deploy.sh status
```

2. API health:

```bash
curl http://localhost:8000/health
```

3. If gateway is deployed separately, verify:

```bash
curl http://localhost:8081/actuator/health
```

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
- Last verified: 2026-02-12
- Canonical docs index: `README.md`
- Canonical map: `CANONICAL.md`
