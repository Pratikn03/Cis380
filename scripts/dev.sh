#!/bin/bash
# Boots the local dev stack:
#   1. docker compose -f docker-compose.dev.yml up -d   (postgres + redis)
#   2. uvicorn app.main:app                              (FastAPI on :8000)
#   3. cd ui-web/frontend && npm run dev                 (Vite on :5173)
#
# Backend uses APP_ENV=development → loads .env.development.
# Ctrl-C stops uvicorn + vite. Postgres + Redis stay running; use `make dev-down`
# to stop them.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

API_PORT="${API_PORT:-8000}"
WEB_PORT="${WEB_PORT:-5173}"

# 1. Local infra
if command -v docker >/dev/null 2>&1; then
    echo "[dev] Starting Postgres + Redis (docker-compose.dev.yml)..."
    docker compose -f docker-compose.dev.yml up -d
else
    echo "[dev] WARNING: docker not found; skipping Postgres + Redis. Set DATABASE_URL/REDIS_URL manually."
fi

# 2. Backend
if [ -f ".venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
fi

# Stop anything bound to the API port already.
if lsof -ti ":${API_PORT}" >/dev/null 2>&1; then
    echo "[dev] Freeing port ${API_PORT}..."
    lsof -ti ":${API_PORT}" | xargs kill -9 || true
fi

PIDS=()
cleanup() {
    echo
    echo "[dev] Stopping backend + frontend..."
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null || true
    echo "[dev] Done. (Postgres + Redis still running. 'make dev-down' to stop them.)"
}
trap cleanup INT TERM EXIT

export APP_ENV=development
export COPYFILE_DISABLE=1

echo "[dev] Starting FastAPI backend on :${API_PORT}..."
python -m uvicorn app.main:app --host 127.0.0.1 --port "${API_PORT}" --reload &
PIDS+=($!)

# 3. Frontend
echo "[dev] Starting Vite frontend on :${WEB_PORT}..."
(cd ui-web/frontend && npm run dev -- --port "${WEB_PORT}" --host 127.0.0.1) &
PIDS+=($!)

echo
echo "[dev] Backend  → http://127.0.0.1:${API_PORT}"
echo "[dev] Frontend → http://127.0.0.1:${WEB_PORT}"
echo "[dev] Press Ctrl-C to stop."
wait
