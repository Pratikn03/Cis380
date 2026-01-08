#!/usr/bin/env bash
set -euo pipefail

MLFLOW_PORT="${MLFLOW_PORT:-5000}"
MLFLOW_HOST="${MLFLOW_HOST:-0.0.0.0}"
MLFLOW_BACKEND="${MLFLOW_BACKEND:-sqlite:///mlflow.db}"
MLFLOW_ARTIFACT_ROOT="${MLFLOW_ARTIFACT_ROOT:-./runs/mlflow}"

echo "Starting MLflow server on ${MLFLOW_HOST}:${MLFLOW_PORT}"
mlflow server \
  --backend-store-uri "${MLFLOW_BACKEND}" \
  --default-artifact-root "${MLFLOW_ARTIFACT_ROOT}" \
  --host "${MLFLOW_HOST}" \
  --port "${MLFLOW_PORT}"
