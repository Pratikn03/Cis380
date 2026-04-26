# Model Card: behavior-anomaly

## Overview
- Domain: behavior
- Version: 1.0.0
- Framework: sklearn
- Artifact: artifacts/release/behavior/122b231/behavior_lof.pkl
- Artifact SHA256: 626d79c4d2ebbef57719be83356346e3bcca56de59b2abc856dca8be08545f52
- Training git SHA: 122b231
- Dataset: data/raw/behavior
- Dataset version: 4d8c04c584adf3b8

## Intended Use
Production inference for the Sentifargo anomaly intelligence platform.

## Metrics
{
  "autoencoder_f1": 0.416988416988417,
  "autoencoder_fpr": 0.03165438980688831,
  "autoencoder_roc_auc": 0.6993122473276316
}

## Data
Training/evaluation data source: `data/raw/behavior`.

## Limitations
Metrics reflect the local curated datasets and must be revalidated after data, feature, or dependency changes.

## Ethical Risks
Model outputs can affect fraud, security, content, or user-risk decisions. Use calibrated thresholds, human review for high-impact actions, and monitor drift and subgroup performance.
