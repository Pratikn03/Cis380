"""
SHAP explainability utilities for fraud models (v1).

Note: This module requires the `shap` package. Install via:
    pip install shap
"""

from typing import Optional

import numpy as np
import pandas as pd

try:
    import shap
except ImportError:  # pragma: no cover
    shap = None


def compute_shap_values(model, X: pd.DataFrame):
    """
    Compute SHAP values for a fitted tree-based model and a feature matrix X.

    Parameters
    ----------
    model : fitted model
        Tree-based model with predict_proba or decision_function.
    X : pd.DataFrame
        Feature matrix.

    Returns
    -------
    explainer, shap_values
    """
    if shap is None:
        raise ImportError("shap is not installed. Please install it with `pip install shap`.")

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    return explainer, shap_values


def plot_shap_summary(model, X: pd.DataFrame, max_display: int = 20, class_index: Optional[int] = None):
    """
    Plot a SHAP summary plot for the given model and dataset.

    For binary classification, shap_values may be a list of length 2.
    """
    if shap is None:
        raise ImportError("shap is not installed. Please install it with `pip install shap`.")

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    if isinstance(shap_values, list):
        # For binary classification, use the explanation for the positive class
        if class_index is None:
            class_index = 1
        shap.summary_plot(shap_values[class_index], X, max_display=max_display)
    else:
        shap.summary_plot(shap_values, X, max_display=max_display)
