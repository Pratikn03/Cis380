"""
Unsupervised anomaly detection models for fraud (v1).

This module implements a simple Isolation Forest wrapper for anomaly scores.
"""

from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


def train_isolation_forest(
    X: pd.DataFrame,
    random_state: int = 42,
    contamination: float = 0.01,
) -> Tuple[IsolationForest, StandardScaler]:
    """
    Train an Isolation Forest model on feature data.

    Parameters
    ----------
    X : pd.DataFrame
        Feature table (no target column).
    random_state : int
        Random seed for reproducibility.
    contamination : float
        Expected proportion of outliers in the data.

    Returns
    -------
    model : IsolationForest
        Fitted isolation forest model.
    scaler : StandardScaler
        Fitted scaler used to normalize features before training.
    """
    numeric_X, imputer_values = _prep_numeric_features(X)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(numeric_X.values)
    scaler.feature_columns_ = list(numeric_X.columns)
    scaler.imputer_values_ = imputer_values.to_dict()

    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(X_scaled)
    return model, scaler


def _prep_numeric_features(X: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Keep only numeric columns with at least one observed value and fill NaNs with medians."""
    numeric = X.select_dtypes(include=[np.number]).copy()
    usable = [col for col in numeric.columns if numeric[col].notna().any()]
    if not usable:
        raise ValueError("No numeric features with observed values found for Isolation Forest.")
    numeric = numeric[usable]
    median_vals = numeric.median(skipna=True)
    numeric = numeric.fillna(median_vals)
    return numeric, median_vals

def compute_anomaly_score(model: IsolationForest, scaler: StandardScaler, X: pd.DataFrame) -> np.ndarray:
    """
    Compute anomaly scores from a trained Isolation Forest model.

    The IsolationForest's decision_function returns higher scores for inliers
    and lower scores for outliers. We invert and normalize to [0, 1] so that
    higher values indicate "more anomalous".

    Returns
    -------
    scores : np.ndarray
        Array of anomaly scores in [0, 1].
    """
    cols = getattr(scaler, "feature_columns_", None)
    if cols is None:
        cols = X.select_dtypes(include=[np.number]).columns.tolist()
    X_numeric = X.loc[:, [c for c in cols if c in X.columns]]
    if X_numeric.shape[1] == 0:
        raise ValueError("Isolation Forest features missing from provided data.")
    imputer_values = getattr(scaler, "imputer_values_", None)
    if imputer_values:
        for col, val in imputer_values.items():
            if col in X_numeric.columns:
                X_numeric[col] = X_numeric[col].fillna(val)
    X_scaled = scaler.transform(X_numeric.values)
    # decision_function: higher = more normal, lower = more abnormal
    raw_scores = model.decision_function(X_scaled)
    # Convert to anomaly-like scores
    inv_scores = -raw_scores
    # Normalize to [0, 1]
    min_s, max_s = inv_scores.min(), inv_scores.max()
    if max_s - min_s < 1e-12:
        return np.zeros_like(inv_scores)
    norm_scores = (inv_scores - min_s) / (max_s - min_s)
    return norm_scores
