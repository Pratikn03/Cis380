#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TS="$(date +"%Y%m%d_%H%M%S")"
OUT="reports/audit_${TS}"
mkdir -p "$OUT"

echo "Writing audit output to: $OUT"

# ---------- 0) Environment snapshot ----------
{
  echo "DATE: $(date)"
  echo "PWD: $(pwd)"
  echo "GIT: $(git rev-parse --short HEAD || true)"
  echo "PYTHON: $(python --version || true)"
  echo "NODE: $(node --version || true)"
  echo "DOCKER: $(docker --version || true)"
} | tee "$OUT/00_env.txt"

# ---------- 1) Repo hygiene (tracked pollution scan) ----------
git status -sb | tee "$OUT/01_git_status.txt" || true
git ls-files | rg -n "node_modules|dist|\\.next|mlartifacts|mlruns|runs|data/raw|data/processed|data/embeddings|models|logs" \
  | tee "$OUT/01_tracked_pollution_hits.txt" || true

# ---------- 2) Static checks ----------
(ruff check app tests || true) | tee "$OUT/02_ruff.txt"
(black --check app tests || true) | tee "$OUT/02_black.txt"
(mypy app --ignore-missing-imports || true) | tee "$OUT/02_mypy.txt"

# ---------- 3) Unit tests ----------
(pytest -q || true) | tee "$OUT/03_pytest.txt"

# ---------- 4) Boot stack (docker) ----------
(docker compose -f docker-compose.elite.yml up -d || true) | tee "$OUT/04_compose_up.txt"
(docker compose -f docker-compose.elite.yml ps || true) | tee "$OUT/04_compose_ps.txt"

# ---------- 5) API health + OpenAPI + metrics ----------
# Wait up to ~60s for API
for i in {1..30}; do
  if curl -sSf http://localhost:8000/api/health >/dev/null 2>&1; then
    echo "API is up" | tee "$OUT/05_api_up.txt"
    break
  fi
  sleep 2
done

(curl -sS http://localhost:8000/api/health || true) | tee "$OUT/05_health.json"
(curl -sS http://localhost:8000/openapi.json | head -n 40 || true) | tee "$OUT/05_openapi_head.txt"
(curl -sS http://localhost:8000/metrics | head -n 80 || true) | tee "$OUT/05_metrics_head.txt"

# ---------- 6) /api/v1 contract quick probe ----------
ADMIN_USER="${ADMIN_USERNAME:-admin}"
ADMIN_PASS="${ADMIN_PASSWORD:-changeme}"
AUTH_JSON="$(curl -sS -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"${ADMIN_USER}\",\"password\":\"${ADMIN_PASS}\"}" || true)"
export AUTH_JSON

TOKEN="$(python - <<'PY' 2>/dev/null || true
import json, os, sys
payload = os.environ.get("AUTH_JSON", "")
try:
    data = json.loads(payload) if payload else {}
    token = data.get("access_token", "")
    print(token)
except Exception:
    print("")
PY
)"

curl_auth() {
  if [ -n "$TOKEN" ]; then
    curl "$@" -H "Authorization: Bearer ${TOKEN}"
  else
    curl "$@"
  fi
}

(curl_auth -sS "http://localhost:8000/api/v1/jobs?limit=3" || true) \
  | tee "$OUT/06_jobs_list.json"

# ---------- 7) RAG roundtrip ----------
(curl_auth -sS -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What does this project do?","top_k":5}' || true) | tee "$OUT/07_rag_query.json"

# ---------- 8) Worker logs ----------
(docker compose -f docker-compose.elite.yml logs --tail=200 worker 2>/dev/null || true) \
  | tee "$OUT/08_worker_tail.txt"
(docker compose -f docker-compose.elite.yml logs --tail=200 api 2>/dev/null || true) \
  | tee "$OUT/08_api_tail.txt"

# ---------- 9) Next.js build ----------
if [ -d "ui-web/next" ]; then
  (cd ui-web/next && npm ci && npm run build || true) | tee "$OUT/09_next_build.txt"
else
  echo "ui-web/next missing" | tee "$OUT/09_next_build.txt"
fi

# ---------- 10) Reproducibility proof (pick ONE) ----------
(python src/pipeline/train_models.py --config configs/fraud_baseline.yaml || true) \
  | tee "$OUT/10_train_run1.txt"
(python src/pipeline/train_models.py --config configs/fraud_baseline.yaml || true) \
  | tee "$OUT/10_train_run2.txt"

# ---------- 11) DVC sanity ----------
(dvc status || true) | tee "$OUT/11_dvc_status.txt"
(dvc remote list || true) | tee "$OUT/11_dvc_remote.txt"

# ---------- 12) Summary marker ----------
echo "DONE: $OUT" | tee "$OUT/99_done.txt"
