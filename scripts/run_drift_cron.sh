#!/usr/bin/env bash
set -euo pipefail

python - << 'PY'
from app.monitoring.service import get_drift_report

report = get_drift_report(1000)
print(report)
PY
