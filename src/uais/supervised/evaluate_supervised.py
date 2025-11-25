"""Evaluation utilities for supervised models."""
from typing import Dict, Tuple

import numpy as np
from sklearn.metrics import confusion_matrix

from uais.utils.metrics import classification_metrics


def evaluate_supervised(model, X, y) -> Tuple[Dict[str, float], np.ndarray]:
    y_pred = model.predict(X)
    y_proba = None
    if hasattr(model, "predict_proba"):
        try:
            y_proba = model.predict_proba(X)[:, 1]
        except Exception:
            y_proba = None
    metrics = classification_metrics(y, y_pred, y_proba)
    cm = confusion_matrix(y, y_pred)
    return metrics, cm


__all__ = ["evaluate_supervised"]
