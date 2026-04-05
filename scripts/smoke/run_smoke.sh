#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
AUTH_HEADER=()
if [[ -n "${AUTH_TOKEN:-}" ]]; then
  AUTH_HEADER=(-H "Authorization: Bearer ${AUTH_TOKEN}")
fi

echo "[SMOKE] Base URL: ${BASE_URL}"

echo "[SMOKE] GET /api/health"
curl -sS "${AUTH_HEADER[@]}" "${BASE_URL}/api/health" | head -c 400; echo

echo "[SMOKE] POST /api/chat"
curl -sS "${AUTH_HEADER[@]}" -X POST "${BASE_URL}/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message":"hello","user_id":"smoke","use_rag":false}' | head -c 400; echo

echo "[SMOKE] POST /api/fraud"
curl -sS "${AUTH_HEADER[@]}" -X POST "${BASE_URL}/api/fraud" \
  -H "Content-Type: application/json" \
  -d '{"features":[0.12,0.8,-1.4,0.2,0.9,0.05,0.33,0.7]}' | head -c 400; echo

echo "[SMOKE] POST /api/recommend"
curl -sS "${AUTH_HEADER[@]}" -X POST "${BASE_URL}/api/recommend" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"smoke","top_k":3}' | head -c 400; echo

echo "[SMOKE] POST /api/recommend/clothes"
curl -sS "${AUTH_HEADER[@]}" -X POST "${BASE_URL}/api/recommend/clothes" \
  -F "text=summer outfits" | head -c 400; echo

echo "[SMOKE] Done."
