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
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X.values)

    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(X_scaled)
    return model, scaler


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
    X_scaled = scaler.transform(X.values)
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
