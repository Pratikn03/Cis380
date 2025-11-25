"""Placeholder utilities to inspect 30-sequence model outputs."""
from pathlib import Path
from typing import Dict, Tuple

import numpy as np

from .metrics import classification_metrics


def load_predictions(pred_path: Path) -> Tuple[np.ndarray, np.ndarray]:
    data = np.load(pred_path, allow_pickle=True).item()
    return data["y_true"], data["y_prob"]


def summarize_predictions(pred_path: Path) -> Dict[str, float]:
    y_true, y_prob = load_predictions(pred_path)
    return classification_metrics(y_true, y_prob)


__all__ = ["summarize_predictions", "load_predictions"]
