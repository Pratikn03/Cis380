# Model Card: behavior (v20260121)

## Overview
- Model name: behavior
- Version: 20260121
- Status: staging
- Created: 2026-01-21 08:44:37 UTC
- Dataset: data/raw/behavior
- Artifact: models/behavior/behavior_lof.pkl
- Run ID: n/a

## Intended Use
Production inference and evaluation

## Metrics
- autoencoder_accuracy: 0.9427379598028062
- autoencoder_f1: 0.416988416988417
- autoencoder_pr_auc: 0.20115953632942166
- autoencoder_precision: 0.4044943820224719
- autoencoder_recall: 0.4302788844621514
- autoencoder_roc_auc: 0.6993122473276316
- autoencoder_threshold: 0.002964316402209204
- lof_accuracy: 0.9019719378081152
- lof_f1: 0.0
- lof_pr_auc: 0.04759196056124384
- lof_precision: 0.0
- lof_recall: 0.0
- lof_roc_auc: 0.4735217997212821
- lof_threshold: 2.9161568442749513

## Limitations
Performance depends on data quality; validate before deployment.

## Raw Metadata
```json
{
  "autoencoder_roc_auc": 0.6993122473276316,
  "autoencoder_pr_auc": 0.20115953632942166,
  "autoencoder_f1": 0.416988416988417,
  "autoencoder_precision": 0.4044943820224719,
  "autoencoder_recall": 0.4302788844621514,
  "autoencoder_accuracy": 0.9427379598028062,
  "autoencoder_threshold": 0.002964316402209204,
  "lof_roc_auc": 0.4735217997212821,
  "lof_pr_auc": 0.04759196056124384,
  "lof_f1": 0.0,
  "lof_precision": 0.0,
  "lof_recall": 0.0,
  "lof_accuracy": 0.9019719378081152,
  "lof_threshold": 2.9161568442749513
}
```
