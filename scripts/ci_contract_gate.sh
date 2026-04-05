#!/usr/bin/env bash
set -euo pipefail
mkdir -p reports
PORT="${CONTRACT_PORT:-8000}"
uvicorn app.main:app --port "$PORT" --log-level warning &
PID=$!
trap 'kill "$PID" >/dev/null 2>&1 || true' EXIT
sleep 2
curl -s "http://localhost:${PORT}/openapi.json" > reports/openapi.json
python scripts/contract_diff.py
echo "Contract gate passed (reports/CONTRACT_DIFF.md generated)"
