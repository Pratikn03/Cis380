"""Simple stacked generalization utilities."""
from typing import Dict, List, Tuple

import numpy as np
from sklearn.linear_model import LogisticRegression

from uais.utils.metrics import classification_metrics


def stack_predictions(base_scores: Dict[str, np.ndarray], labels: np.ndarray) -> Tuple[LogisticRegression, Dict[str, float]]:
    keys = sorted(base_scores)
    X = np.column_stack([base_scores[k] for k in keys])
    y = np.asarray(labels)[: X.shape[0]]
    meta = LogisticRegression(max_iter=200, class_weight="balanced")
    meta.fit(X, y)
    y_pred = meta.predict(X)
    y_proba = meta.predict_proba(X)[:, 1]
    metrics = classification_metrics(y, y_pred, y_proba)
    metrics = {f"stack_{k}": v for k, v in metrics.items()}
    return meta, metrics


__all__ = ["stack_predictions"]
