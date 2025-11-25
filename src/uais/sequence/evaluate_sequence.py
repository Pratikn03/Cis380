"""Evaluation helpers for sequence models."""
from typing import Dict

import numpy as np

from uais.utils.metrics import classification_metrics


def evaluate_sequence_predictions(y_true, y_scores) -> Dict[str, float]:
    y_true = np.asarray(y_true)
    y_scores = np.asarray(y_scores)
    y_pred = (y_scores >= 0.5).astype(int)
    return classification_metrics(y_true, y_pred, y_scores)


__all__ = ["evaluate_sequence_predictions"]
