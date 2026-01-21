# Model Card: cyber (v20260121)

## Overview
- Model name: cyber
- Version: 20260121
- Status: staging
- Created: 2026-01-21 08:44:37 UTC
- Dataset: data/raw/cyber
- Artifact: models/cyber/supervised/cyber_model.pkl
- Run ID: n/a

## Intended Use
Production inference and evaluation

## Metrics
- anomaly: {'roc_auc': 0.21939528693247162, 'pr_auc': 0.5771866084848896, 'f1': 0.041818427087548904, 'precision': 0.5340223944875108, 'recall': 0.021761257941104208, 'accuracy': 0.2897}
- test: {'roc_auc': 0.9938023973491984, 'pr_auc': 0.9974662226193255, 'f1': 0.9717891223861918, 'precision': 0.962603305785124, 'recall': 0.9811519427187533, 'accuracy': 0.959425}
- val: {'roc_auc': 0.9941095292967979, 'pr_auc': 0.9976055413133372, 'f1': 0.9725641560609222, 'precision': 0.9636507717750827, 'recall': 0.9816439702372596, 'accuracy': 0.96055}

## Limitations
Performance depends on data quality; validate before deployment.

## Raw Metadata
```json
{
  "val": {
    "roc_auc": 0.9941095292967979,
    "pr_auc": 0.9976055413133372,
    "f1": 0.9725641560609222,
    "precision": 0.9636507717750827,
    "recall": 0.9816439702372596,
    "accuracy": 0.96055
  },
  "test": {
    "roc_auc": 0.9938023973491984,
    "pr_auc": 0.9974662226193255,
    "f1": 0.9717891223861918,
    "precision": 0.962603305785124,
    "recall": 0.9811519427187533,
    "accuracy": 0.959425
  },
  "anomaly": {
    "roc_auc": 0.21939528693247162,
    "pr_auc": 0.5771866084848896,
    "f1": 0.041818427087548904,
    "precision": 0.5340223944875108,
    "recall": 0.021761257941104208,
    "accuracy": 0.2897
  }
}
```
