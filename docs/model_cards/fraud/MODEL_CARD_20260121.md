# Model Card: fraud (v20260121)

## Overview
- Model name: fraud
- Version: 20260121
- Status: staging
- Created: 2026-01-21 08:44:37 UTC
- Dataset: data/raw/fraud
- Artifact: models/fraud/supervised/fraud_model.pkl
- Run ID: n/a

## Intended Use
Production inference and evaluation

## Metrics
- hybrid: {'roc_auc': 0.9581045138261606, 'pr_auc': 0.6224547367906189, 'f1': 0.7079646017699115, 'precision': 0.6299212598425197, 'recall': 0.8080808080808081, 'accuracy': 0.9988413328183702}
- test: {'roc_auc': 0.8920228612559301, 'pr_auc': 0.5918362979092672, 'f1': 0.7079646017699115, 'precision': 0.6299212598425197, 'recall': 0.8080808080808081, 'accuracy': 0.9988413328183702}
- val: {'roc_auc': 0.8916427130442772, 'pr_auc': 0.5226038177281577, 'f1': 0.6636363636363637, 'precision': 0.5983606557377049, 'recall': 0.7448979591836735, 'accuracy': 0.998700865504468}

## Limitations
Performance depends on data quality; validate before deployment.

## Raw Metadata
```json
{
  "val": {
    "roc_auc": 0.8916427130442772,
    "pr_auc": 0.5226038177281577,
    "f1": 0.6636363636363637,
    "precision": 0.5983606557377049,
    "recall": 0.7448979591836735,
    "accuracy": 0.998700865504468
  },
  "test": {
    "roc_auc": 0.8920228612559301,
    "pr_auc": 0.5918362979092672,
    "f1": 0.7079646017699115,
    "precision": 0.6299212598425197,
    "recall": 0.8080808080808081,
    "accuracy": 0.9988413328183702
  },
  "hybrid": {
    "roc_auc": 0.9581045138261606,
    "pr_auc": 0.6224547367906189,
    "f1": 0.7079646017699115,
    "precision": 0.6299212598425197,
    "recall": 0.8080808080808081,
    "accuracy": 0.9988413328183702
  }
}
```
