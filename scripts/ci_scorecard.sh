#!/usr/bin/env bash
set -euo pipefail

PORT="${SCORECARD_PORT:-8000}"
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

BASE_URL="${BASE_URL}" SCORECARD_STRICT="${SCORECARD_STRICT:-false}" python scripts/system_scorecard.py
BASE_URL="${BASE_URL}" python scripts/rag/evaluate_dsa.py || true
