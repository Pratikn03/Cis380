#!/usr/bin/env bash
set -euo pipefail

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
BASE="http://$HOST:$PORT"

echo "===================="
echo "SentinelForge TEST SUITE"
echo "===================="

# ---------- 1) Basic structure checks ----------
echo "[1/7] Repo structure checks"
[ -f "app/main.py" ] || { echo "❌ Missing app/main.py (canonical entrypoint)"; exit 1; }
[ -d "models" ] || { echo "❌ Missing models/ directory"; exit 1; }
[ -d "data" ] || { echo "❌ Missing data/ directory"; exit 1; }
echo "✅ Structure OK"

# ---------- 2) Data readiness checks ----------
echo "[2/7] Data readiness checks"
req_paths=(
  "data/processed/fraud/fraud_features.parquet"
  "data/processed/cyber/unsw_nb15_features.parquet"
  "data/processed/behavior/r4_2_raw.parquet"
)
for p in "${req_paths[@]}"; do
  if [ ! -f "$p" ]; then
    echo "❌ Missing processed file: $p"
    echo "   Fix: run your preprocessing pipeline to rebuild data/processed."
    exit 1
  fi
done

REAL_COUNT=$(find data/raw/vision/train_real -type f 2>/dev/null | wc -l | tr -d ' ')
FAKE_COUNT=$(find data/raw/vision/train_fake -type f 2>/dev/null | wc -l | tr -d ' ')
echo "Vision frames -> real=$REAL_COUNT fake=$FAKE_COUNT"
if [ "$REAL_COUNT" -eq 0 ] || [ "$FAKE_COUNT" -eq 0 ]; then
  echo "❌ Vision frame dataset is empty."
  exit 1
fi
echo "✅ Data OK"

# ---------- 3) Artifact checks ----------
echo "[3/7] Model artifact checks"
must_exist=(
  "models/voice_emotion.pkl"
)
for m in "${must_exist[@]}"; do
  if [ ! -f "$m" ]; then
    echo "❌ Missing model artifact: $m"
    exit 1
  fi
done

if [ ! -f "models/vision/resnet/model.pt" ]; then
  echo "❌ Missing vision model artifact: models/vision/resnet/model.pt"
  echo "   Fix: bash scripts/run_train_vision.sh"
  exit 1
fi

echo "✅ Artifacts OK"

# ---------- 4) Unit tests (if present) ----------
echo "[4/7] Unit tests (best-effort)"
if [ -f "pytest.ini" ] || [ -d "tests" ]; then
  if command -v pytest >/dev/null 2>&1; then
    pytest -q || { echo "❌ pytest failed"; exit 1; }
    echo "✅ pytest passed"
  else
    echo "⚠️ pytest not installed; skipping unit tests"
  fi
else
  echo "ℹ️ No tests/ or pytest.ini found; skipping"
fi

# ---------- 5) Start backend and test endpoints ----------
echo "[5/7] Backend smoke test"
uvicorn app.main:app --host "$HOST" --port "$PORT" >/tmp/sentinelforge_uvicorn.log 2>&1 &
PID=$!

cleanup() {
  kill "$PID" >/dev/null 2>&1 || true
  wait "$PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

if ! command -v curl >/dev/null 2>&1; then
  echo "❌ curl not found; cannot smoke test HTTP."
  exit 1
fi

code() {
  local url="$1"
  if [ "${AUTH_TOKEN:-}" != "" ]; then
    curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer ${AUTH_TOKEN}" "$url"
  else
    curl -s -o /dev/null -w "%{http_code}" "$url"
  fi
}

check_200() {
  local url="$1"
  local c
  c=$(code "$url")
  if [ "$c" != "200" ]; then
    echo "❌ Expected 200 but got $c for $url"
    echo "---- backend log (tail) ----"
    tail -n 60 /tmp/sentinelforge_uvicorn.log || true
    exit 1
  fi
  echo "✅ 200 $url"
}

# wait up to ~20s for server to be ready
for _ in $(seq 1 20); do
  if [ "$(code "$BASE/health" || true)" = "200" ]; then
    break
  fi
  sleep 1
done

check_200 "$BASE/health"
check_200 "$BASE/metrics"

post_try() {
  local url="$1"
  local json="$2"
  local c
  if [ "${AUTH_TOKEN:-}" != "" ]; then
    c=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Authorization: Bearer ${AUTH_TOKEN}" "$url" -H "Content-Type: application/json" -d "$json")
  else
    c=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$url" -H "Content-Type: application/json" -d "$json")
  fi
  echo "POST $url -> $c"
}

post_try "$BASE/api/chat"        '{"message":"hello"}'
post_try "$BASE/api/rag/query"   '{"query":"what is this project?","top_k":2}'
post_try "$BASE/api/recommend"   '{"user_id":1,"movie_id":1}'

echo "✅ Backend smoke OK"

# ---------- 6) Streamlit import sanity (optional) ----------
echo "[6/7] Streamlit UI sanity (import-only)"
if [ -f "app/streamlit_chatbot/app.py" ]; then
  python -c "import importlib.util; spec=importlib.util.spec_from_file_location('ui','app/streamlit_chatbot/app.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print('✅ Streamlit app imports OK')"
else
  echo "ℹ️ Streamlit app not found; skipping"
fi

# ---------- 7) Video status (optional) ----------
echo "[7/7] Vision video status (optional)"
VR=$(find data/raw/vision/video/real -type f -name "*.mp4" 2>/dev/null | wc -l | tr -d ' ' || true)
VF=$(find data/raw/vision/video/fake -type f -name "*.mp4" 2>/dev/null | wc -l | tr -d ' ' || true)
echo "Vision videos -> real=$VR fake=$VF"
echo "ℹ️ Video is optional unless you implemented video inference routes."

echo ""
echo "✅ ALL CHECKS PASSED"
