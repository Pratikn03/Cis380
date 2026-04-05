#!/usr/bin/env bash
set -euo pipefail

echo "[fraud] running supervised + anomaly experiment"
python src/scripts/run_fraud_experiment.py

echo "[cyber] running supervised + anomaly experiment"
python src/scripts/run_cyber_experiment.py

echo "[behavior] running autoencoder + LOF experiment"
python src/scripts/run_behavior_experiment.py

echo "[fusion] stacking domain scores"
python src/scripts/run_fusion_experiment.py
