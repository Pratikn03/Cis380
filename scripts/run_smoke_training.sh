#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [[ ! -x ".venv/bin/python" ]]; then
  echo "Missing .venv/bin/python. Create the venv first:"
  echo "  python3.11 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt -r requirements-ci.txt"
  exit 1
fi

export PYTHONPATH="${REPO_ROOT}/src"
export XDG_CACHE_HOME="${REPO_ROOT}/.cache"
export MPLCONFIGDIR="${REPO_ROOT}/.cache/matplotlib"
mkdir -p "${XDG_CACHE_HOME}" "${MPLCONFIGDIR}"

echo "[1/3] Cyber smoke training"
export Sentifargo_CYBER_SAMPLE_SIZE="${Sentifargo_CYBER_SAMPLE_SIZE:-1000}"
.venv/bin/python -u src/scripts/run_cyber_experiment.py

echo "[2/3] Behavior smoke training"
export BEHAVIOR_DATA_PATH="${BEHAVIOR_DATA_PATH:-data/raw/behavior/online_shoppers_intention.csv}"
export Sentifargo_BEHAVIOR_SAMPLE_SIZE="${Sentifargo_BEHAVIOR_SAMPLE_SIZE:-5000}"
export BEHAVIOR_AUGMENT_INSIDER="${BEHAVIOR_AUGMENT_INSIDER:-false}"
.venv/bin/python -u src/scripts/run_behavior_experiment.py

echo "[3/3] Fraud smoke training"
export Sentifargo_FRAUD_SAMPLE_SIZE="${Sentifargo_FRAUD_SAMPLE_SIZE:-20000}"
export Sentifargo_FRAUD_MAX_ITER="${Sentifargo_FRAUD_MAX_ITER:-50}"
export Sentifargo_FRAUD_SKIP_PLOTS="${Sentifargo_FRAUD_SKIP_PLOTS:-true}"
.venv/bin/python -u src/scripts/run_fraud_experiment.py

echo "Smoke training complete."
