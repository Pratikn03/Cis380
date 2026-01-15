#!/usr/bin/env bash
set -euo pipefail

PORT="${E2E_PORT:-8000}"
BASE_URL="http://localhost:${PORT}"

uvicorn app.main:app --port "$PORT" --log-level warning &
PID=$!
trap 'kill "$PID" >/dev/null 2>&1 || true' EXIT

for _ in {1..20}; do
  if curl -sf "${BASE_URL}/api/health" >/dev/null; then
    break
  fi
  sleep 1
done

BASE_URL="${BASE_URL}" pytest tests/e2e/test_smoke.py -q
