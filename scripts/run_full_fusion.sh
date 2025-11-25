#!/usr/bin/env bash
set -euo pipefail
# Sequentially run domain flows then fusion
python - <<'PY'
from src.orchestration.fraud_flow import fraud_pipeline
from src.orchestration.cyber_flow import cyber_pipeline
from src.orchestration.behavior_flow import behavior_pipeline
from src.orchestration.nlp_flow import nlp_pipeline
from src.orchestration.vision_flow import vision_pipeline
from src.orchestration.fusion_flow import fusion_pipeline

# Run flows (best effort; they contain fallbacks where data is missing)
fraud_pipeline()
cyber_pipeline()
behavior_pipeline()
nlp_pipeline()
vision_pipeline()
fusion_pipeline()
PY
