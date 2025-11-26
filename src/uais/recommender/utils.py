"""Utility helpers for the recommender layer."""
from __future__ import annotations

import json
from typing import Any, Dict, Iterable

import numpy as np


def safe_float(val: Any, default: float = 0.0) -> float:
    try:
        return float(val)
    except Exception:
        return default


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + np.exp(-x))


def align_features_for_model(model, features: Dict[str, Any]) -> np.ndarray:
    """Align a feature dict to a model expecting column names.

    If the model has a `feature_names_in_` attribute, use that ordering.
    Otherwise, return a single-row array of all numeric values in sorted-key order.
    """
    if hasattr(model, "feature_names_in_"):
        cols = list(model.feature_names_in_)
        row = [safe_float(features.get(c, 0.0), 0.0) for c in cols]
        return np.array(row, dtype=float).reshape(1, -1)

    # Fallback: use numeric-ish values sorted by key
    cols = sorted(features.keys())
    row = [safe_float(features[k], 0.0) for k in cols]
    return np.array(row, dtype=float).reshape(1, -1)


def try_parse_json(text: str) -> Dict[str, Any]:
    """Best-effort JSON or Python-literal parse of user input."""
    try:
        return json.loads(text)
    except Exception:
        try:
            import ast

            return ast.literal_eval(text)
        except Exception:
            return {}


__all__ = ["safe_float", "sigmoid", "align_features_for_model", "try_parse_json"]
