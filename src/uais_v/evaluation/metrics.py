"""Binary/softmax metric helpers for UAIS-V models."""
from typing import Dict

import numpy as np
from sklearn import metrics


def classification_metrics(y_true, y_prob, threshold: float = 0.5) -> Dict[str, float]:
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)

    if y_prob.ndim > 1 and y_prob.shape[1] > 1:
        # assume class 1 probability
        y_prob = y_prob[:, 1]

    y_pred = (y_prob >= threshold).astype(int)

    scores: Dict[str, float] = {}
    try:
        scores["roc_auc"] = metrics.roc_auc_score(y_true, y_prob)
    except ValueError:
        scores["roc_auc"] = float("nan")

    try:
        scores["pr_auc"] = metrics.average_precision_score(y_true, y_prob)
    except ValueError:
        scores["pr_auc"] = float("nan")

    scores["f1"] = metrics.f1_score(y_true, y_pred, zero_division=0)
    scores["precision"] = metrics.precision_score(y_true, y_pred, zero_division=0)
    scores["recall"] = metrics.recall_score(y_true, y_pred, zero_division=0)
    scores["accuracy"] = metrics.accuracy_score(y_true, y_pred)
    return scores


__all__ = ["classification_metrics"]
