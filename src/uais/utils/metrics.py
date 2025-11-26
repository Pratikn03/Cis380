"""
Shared metric utilities for fraud / anomaly models.
"""

from typing import Dict

import numpy as np
from sklearn import metrics


def compute_classification_metrics(y_true: np.ndarray, y_prob: np.ndarray, threshold: float = 0.5) -> Dict[str, float]:
    """
    Compute common binary classification metrics for fraud detection.

    Parameters
    ----------
    y_true : array-like
        Ground truth labels (0/1).
    y_prob : array-like
        Predicted probabilities for the positive class (fraud).
    threshold : float
        Threshold to convert probabilities into hard labels.

    Returns
    -------
    scores : dict
        Contains keys: 'roc_auc', 'pr_auc', 'f1', 'precision', 'recall', 'accuracy'.
    """
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)

    # Hard labels
    y_pred = (y_prob >= threshold).astype(int)

    scores = {}

    # ROC-AUC
    try:
        scores["roc_auc"] = metrics.roc_auc_score(y_true, y_prob)
    except ValueError:
        scores["roc_auc"] = float("nan")

    # PR-AUC (Average Precision)
    try:
        scores["pr_auc"] = metrics.average_precision_score(y_true, y_prob)
    except ValueError:
        scores["pr_auc"] = float("nan")

    scores["f1"] = metrics.f1_score(y_true, y_pred, zero_division=0)
    scores["precision"] = metrics.precision_score(y_true, y_pred, zero_division=0)
    scores["recall"] = metrics.recall_score(y_true, y_pred, zero_division=0)
    scores["accuracy"] = metrics.accuracy_score(y_true, y_pred)

    return scores


def compute_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
    """
    Compute confusion matrix (2x2 for binary classification).

    Returns
    -------
    cm : np.ndarray
        Confusion matrix: [[tn, fp], [fn, tp]]
    """
    return metrics.confusion_matrix(y_true, y_pred)


# Backwards-compatible aliases for other modules
classification_metrics = compute_classification_metrics

def anomaly_metrics(y_true, scores, threshold=None, contamination: float = 0.05):
    # Simple anomaly metric: threshold by quantile if none provided
    y_true = np.asarray(y_true)
    scores = np.asarray(scores)
    if threshold is None:
        threshold = np.quantile(scores, 1 - contamination)
    preds = (scores >= threshold).astype(int)
    out = classification_metrics(y_true, preds, threshold=0.5)
    out["threshold"] = float(threshold)
    return out


def best_f1_threshold(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """Find probability threshold that maximizes F1 on given labels."""
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    thresholds = np.unique(y_prob)
    if len(thresholds) == 0:
        return 0.5
    best_thr = 0.5
    best_f1 = -1.0
    for thr in thresholds:
        preds = (y_prob >= thr).astype(int)
        f1 = metrics.f1_score(y_true, preds, zero_division=0)
        if f1 > best_f1:
            best_f1 = f1
            best_thr = thr
    return float(best_thr)
