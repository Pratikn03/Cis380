#!/usr/bin/env bash
set -euo pipefail

# Terminal-friendly demo launcher:
# - Starts the backend in the background
# - Starts Streamlit in the foreground

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
BACKEND_URL="${BACKEND_URL:-http://localhost:$PORT}"

if ! command -v uvicorn >/dev/null 2>&1; then
  echo "❌ uvicorn not found in PATH"
  exit 1
fi

if ! command -v streamlit >/dev/null 2>&1; then
  echo "❌ streamlit not found in PATH"
  exit 1
fi

cleanup() {
  if [ -n "${PID:-}" ]; then
    kill "$PID" >/dev/null 2>&1 || true
    wait "$PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

echo "🚀 Starting backend: app.main:app on $HOST:$PORT"
uvicorn app.main:app --host "$HOST" --port "$PORT" >/tmp/Sentifargo_demo_backend.log 2>&1 &
PID=$!
sleep 2

echo "✅ Backend up (log: /tmp/Sentifargo_demo_backend.log)"
echo "🌐 Starting Streamlit UI (Sentifargo_BACKEND=$BACKEND_URL)"
Sentifargo_BACKEND="$BACKEND_URL" streamlit run app/streamlit_chatbot/app.py
