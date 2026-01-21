# Model Card: recommender (v20260121)

## Overview
- Model name: recommender
- Version: 20260121
- Status: staging
- Created: 2026-01-21 08:44:37 UTC
- Dataset: data/raw/recommendation
- Artifact: models/recommender/recommender_model.pkl
- Run ID: n/a

## Intended Use
Production inference and evaluation

## Metrics
- ALLOW: {'precision': 1.0, 'recall': 1.0, 'f1-score': 1.0, 'support': 3331.0}
- BLOCK: {'precision': 1.0, 'recall': 1.0, 'f1-score': 1.0, 'support': 17.0}
- MONITOR: {'precision': 1.0, 'recall': 1.0, 'f1-score': 1.0, 'support': 1.0}
- accuracy: 1.0
- macro avg: {'precision': 1.0, 'recall': 1.0, 'f1-score': 1.0, 'support': 3349.0}
- weighted avg: {'precision': 1.0, 'recall': 1.0, 'f1-score': 1.0, 'support': 3349.0}

## Limitations
Performance depends on data quality; validate before deployment.

## Raw Metadata
```json
{
  "ALLOW": {
    "precision": 1.0,
    "recall": 1.0,
    "f1-score": 1.0,
    "support": 3331.0
  },
  "BLOCK": {
    "precision": 1.0,
    "recall": 1.0,
    "f1-score": 1.0,
    "support": 17.0
  },
  "MONITOR": {
    "precision": 1.0,
    "recall": 1.0,
    "f1-score": 1.0,
    "support": 1.0
  },
  "accuracy": 1.0,
  "macro avg": {
    "precision": 1.0,
    "recall": 1.0,
    "f1-score": 1.0,
    "support": 3349.0
  },
  "weighted avg": {
    "precision": 1.0,
    "recall": 1.0,
    "f1-score": 1.0,
    "support": 3349.0
  }
}
```
