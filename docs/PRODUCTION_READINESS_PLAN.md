# Sentifargo Production Readiness Plan (No Dataset Deletions)

**Constraint acknowledged:** do **not** delete any datasets or files. All actions below respect that constraint.

## Goal
Prepare the system for global production publishing with a clear, minimal-risk checklist and optional improvements.

## Decisions (Confirmed)
- **Production UI:** Next (`ui-web/next`)
- **Auth model:** JWT-first (legacy token optional for backward compatibility)
- **Production stack:** Postgres + Redis + Celery worker included in `docker-compose.production.yml`
- **Production config:** explicit `SECRET_KEY`, `CORS_ORIGINS`, `ALLOWED_HOSTS`, and `FORCE_HTTPS=true`

---

## 1) Release Blockers (Fix Before Global Publish)

### 1.1 Secrets & Access Control
- **Rotate exposed secrets**: a real OpenAI key is present in `.env`. Revoke/rotate and replace with a placeholder.
  - Files: `.env`
- **Require explicit production secret material**: `SECRET_KEY`, `CORS_ORIGINS`, and `ALLOWED_HOSTS` must be set explicitly for production, and `FORCE_HTTPS` must be true.
  - Files: `app/core/config.py`, `docker-compose.production.yml`
- **Bootstrap safety**: `/api/v1/admin/bootstrap` remains one-time gated by `BOOTSTRAP_TOKEN`.
  - Files: `app/api/v1/auth.py`

### 1.2 Production Stack Completeness
- **Database + worker required**: `/api/v1/jobs`, audits, and async task flows rely on DB + Celery, and the production compose now includes Postgres, Redis, and the worker as first-class services.
  - Files: `docker-compose.production.yml`, `app/api/v1/jobs.py`, `app/workers/tasks.py`

### 1.3 External Exposure Safety
- **CORS must be explicit**: default `*` is no longer acceptable for production.
  - Files: `app/core/config.py`, `docker-compose.production.yml`
- **Allowed hosts & HTTPS**: production deployments must define `ALLOWED_HOSTS` and run with HTTPS redirection enabled.
  - Files: `app/core/config.py`, `docker-compose.production.yml`

---

## 2) High-Priority Improvements (Strongly Recommended)

### 2.1 Health Checks That Actually Validate Dependencies
- Health checks now ping Postgres, Redis, and the Celery worker instead of treating filesystem state as the database signal.
  - Files: `app/core/health.py`

### 2.2 Dependency Pinning
- Requirements are `>=` and allow incompatible versions (e.g., pydantic v1 vs v2).
- Pin versions in `requirements.txt` and/or use `requirements.lock` for reproducible builds.
  - Files: `requirements.txt`, `pyproject.toml`

### 2.3 Auth/UI Alignment
- Keep production auth flow aligned to the canonical Next app and gateway GraphQL contract.
  - Files: `ui-web/next/src/app/login/page.tsx`, `ui-web/next/src/lib/auth.ts`, `app/main.py`

---

## 3) Dataset Handling (Keep Everything, But Make It Production-Safe)

You requested **no dataset deletions**. To publish globally while keeping datasets:

- **Add dataset licensing and usage notes** (confirm redistribution rights).
  - Files: `DATASETS.md`, `docs/DATASET_DOWNLOADS.md`
- **Clearly separate “training data” vs “runtime assets”** in docs and deployment.
  - Files: `docs/REPRODUCIBILITY.md`, `docs/DEPLOY_RENDER.md`
- **Optional**: use DVC or LFS metadata for large datasets but keep originals locally.

---

## 4) Observability & Monitoring

- **Grafana dashboards** exist; verify they load and are linked in deployment docs.
  - Files: `deploy/grafana/dashboards/sentifargo.json`
- **Prometheus Redis** scrape requires a Redis exporter (current config points at `redis:6379`).
  - Files: `deploy/prometheus/prometheus.yml`

---

## 5) Release Documentation Cleanup

- README has duplicated/misaligned sections and mixed entrypoints. Clean for public use.
  - Files: `README.md`
- Clarify which backend entrypoint is supported (`app/main.py`) and deprecate root `main.py` for prod.
  - Files: `app/main.py`, `main.py`

---

## 6) Suggested Minimal “Go-Live” Checklist

### Security
- [ ] Rotate all secrets (OpenAI key, JWT secret, Grafana admin password, DB passwords)
- [ ] Keep JWT-first auth aligned across Next and gateway
- [ ] Keep bootstrap endpoint one-time gated by `BOOTSTRAP_TOKEN`

### Infrastructure
- [ ] Confirm Postgres + Redis + Celery worker stay in production compose
- [ ] Run migrations on deploy (`alembic upgrade head`)
- [ ] Configure Nginx SSL certificates

### App Runtime
- [ ] Restrict CORS to explicit production domains
- [ ] Set `ALLOWED_HOSTS` and `FORCE_HTTPS=true`
- [ ] Ensure health checks validate DB + Redis + worker

### UI
- [ ] Select **one** UI for production and ensure auth headers are consistent
- [ ] Confirm API base URLs and auth token storage

---

## 7) Optional Hardening Ideas (If Time Allows)

- Add rate limiting at gateway (Nginx or API key-based throttles)
- Add audit log export or admin dashboard
- Add CI step for dependency vulnerability scanning
- Add automated daily scorecard + report uploads

---

## Current Focus
Apply the decisions above without deleting any datasets and ensure the Next UI can authenticate and run end-to-end.
