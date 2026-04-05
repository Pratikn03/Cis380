"""SHAP helpers with graceful fallback when shap is missing."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)

try:  # shap is optional
    import shap  # type: ignore

    _SHAP_AVAILABLE = True
except Exception as exc:  # pragma: no cover - optional dep
    logger.warning("SHAP not installed, explanations will fallback: %s", exc)
    shap = None  # type: ignore
    _SHAP_AVAILABLE = False


@dataclass
class ShapResult:
    values: Optional[np.ndarray]
    feature_names: List[str]
    model_class: str
    top_features: List[tuple[str, float]]
    note: str


def explain(
    model, X: np.ndarray, feature_names: List[str], top_k: int = 5, force_kernel: bool = False
) -> ShapResult:
    """Return SHAP values (or fallback) for a single-row X."""
    if X.ndim == 1:
        X = X.reshape(1, -1)

    if not _SHAP_AVAILABLE:
        return ShapResult(
            values=None,
            feature_names=feature_names,
            model_class=type(model).__name__,
            top_features=[],
            note="SHAP not installed; install shap to enable plots.",
        )

    try:
        if force_kernel:
            explainer = shap.KernelExplainer(model.predict, X)
        elif hasattr(model, "get_booster") or "XGB" in type(model).__name__:
            explainer = shap.TreeExplainer(model)
        elif hasattr(model, "predict_proba"):
            explainer = shap.TreeExplainer(model)
        else:
            explainer = shap.KernelExplainer(model.predict, X)

        shap_vals = explainer.shap_values(X)
        # handle multiclass list-of-arrays
        if isinstance(shap_vals, list):
            try:
                proba = model.predict_proba(X)[0]
                class_idx = int(np.argmax(proba))
            except Exception:
                class_idx = 0
            shap_vec = np.array(shap_vals[class_idx]).reshape(-1)
        else:
            shap_vec = np.array(shap_vals).reshape(-1)

        order = np.argsort(np.abs(shap_vec))[::-1][:top_k]
        top = [
            (feature_names[i] if i < len(feature_names) else f"f{i}", float(shap_vec[i]))
            for i in order
        ]

        return ShapResult(
            values=shap_vec,
            feature_names=feature_names,
            model_class=type(model).__name__,
            top_features=top,
            note="ok",
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("SHAP explanation failed: %s", exc)
        return ShapResult(
            values=None,
            feature_names=feature_names,
            model_class=type(model).__name__,
            top_features=[],
            note=f"SHAP failed: {exc}",
        )
