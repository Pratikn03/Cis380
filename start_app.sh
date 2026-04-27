#!/bin/bash
# Boots the canonical stack: FastAPI backend (:8000) + Vite frontend (:5173).
# Prefer `make dev` — this script remains for muscle memory.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

API_PORT="${API_PORT:-8000}"
WEB_PORT="${WEB_PORT:-5173}"

if lsof -ti ":${API_PORT}" >/dev/null 2>&1; then
    echo "Freeing port ${API_PORT}..."
    lsof -ti ":${API_PORT}" | xargs kill -9 || true
fi

if [ -f ".venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
fi

echo "Starting FastAPI backend on :${API_PORT}..."
python -m uvicorn app.main:app --host 0.0.0.0 --port "${API_PORT}" &
BACKEND_PID=$!
trap 'kill $BACKEND_PID 2>/dev/null || true' EXIT

sleep 3

echo "Starting Vite frontend on :${WEB_PORT}..."
cd ui-web/frontend
exec npm run dev -- --port "${WEB_PORT}"
