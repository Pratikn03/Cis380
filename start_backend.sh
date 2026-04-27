#!/bin/bash
# Canonical backend launcher. Replaces the old root main.py-based script.
# For full dev (backend + frontend + local infra), use `make dev` instead.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

PORT="${PORT:-8000}"

echo "Starting Sentifargo API (app.main:app) on http://0.0.0.0:${PORT}"

if lsof -ti ":${PORT}" >/dev/null 2>&1; then
    echo "Freeing port ${PORT}..."
    lsof -ti ":${PORT}" | xargs kill -9 || true
fi

if [ -f ".venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
fi

exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT}" "$@"
