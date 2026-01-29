# Sentifargo Production Readiness Plan (No Dataset Deletions)

**Constraint acknowledged:** do **not** delete any datasets or files. All actions below respect that constraint.

## Goal
Prepare the system for global production publishing with a clear, minimal-risk checklist and optional improvements.

## Decisions (Confirmed)
- **Production UI:** React (`ui-web/frontend`)
- **Auth model:** JWT-first (legacy token optional for backward compatibility)
- **Production stack:** Postgres + Celery worker included

---

## 1) Release Blockers (Fix Before Global Publish)

### 1.1 Secrets & Access Control
- **Rotate exposed secrets**: A real OpenAI key is present in `.env`. Revoke/rotate and replace with a placeholder.
  - Files: `.env`
- **Enforce auth globally**: legacy routes allow unauthenticated access when `AUTH_TOKEN` is unset.
  - Files: `app/legacy/api/deps.py`, `app/main.py`
- **Bootstrap safety**: `/api/v1/admin/bootstrap` is unauthenticated until the first user exists. Lock it down or gate behind a one-time token.
  - Files: `app/api/v1/auth.py`

### 1.2 Production Stack Completeness
- **Database + worker required**: `/api/v1/jobs`, audits, and auth rely on DB + Celery. Production compose currently lacks Postgres/worker.
  - Files: `docker-compose.production.yml`, `app/api/v1/jobs.py`, `app/workers/tasks.py`

### 1.3 External Exposure Safety
- **CORS must be explicit**: default `*` is unsafe for global release.
  - Files: `app/core/config.py`, `docker-compose.production.yml`
- **Allowed hosts & HTTPS**: set `ALLOWED_HOSTS` and `FORCE_HTTPS` for public domain.
  - Files: `app/main.py`

---

## 2) High-Priority Improvements (Strongly Recommended)

### 2.1 Health Checks That Actually Validate Dependencies
- Current DB check only verifies `./data`. Replace with an actual DB ping in health checks.
  - Files: `app/core/health.py`

### 2.2 Dependency Pinning
- Requirements are `>=` and allow incompatible versions (e.g., pydantic v1 vs v2).
- Pin versions in `requirements.txt` and/or use `requirements.lock` for reproducible builds.
  - Files: `requirements.txt`, `pyproject.toml`

### 2.3 Auth/UI Alignment
- React UI expects `localStorage.token`, Next UI expects JWT from `/api/v1/auth/login`. Align on **one** UI and **one** auth flow.
  - Files: `ui-web/frontend/src/services/api.ts`, `ui-web/next/src/app/login/page.tsx`, `app/main.py`

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
- [ ] Enforce JWT-only auth (disable legacy auth bypass)
- [ ] Disable or gate bootstrap endpoint

### Infrastructure
- [ ] Add Postgres + Celery worker to production compose OR remove job endpoints
- [ ] Run migrations on deploy (`alembic upgrade head`)
- [ ] Configure Nginx SSL certificates

### App Runtime
- [ ] Restrict CORS to production domains
- [ ] Set `ALLOWED_HOSTS` and `FORCE_HTTPS=true`
- [ ] Ensure health checks validate DB + Redis

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
Apply the decisions above without deleting any datasets and ensure the React UI can authenticate and run end-to-end.
