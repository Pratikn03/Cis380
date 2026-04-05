"""
Simple blending utilities to combine supervised probabilities and anomaly scores.
"""

import numpy as np


def blend_supervised_and_anomaly(
    p_supervised: np.ndarray,
    anomaly_scores: np.ndarray,
    alpha: float = 0.7,
    beta: float = 0.3,
) -> np.ndarray:
    """
    Blend supervised fraud probabilities with anomaly scores into a final risk score.

    Parameters
    ----------
    p_supervised : np.ndarray
        Predicted probabilities from a supervised model (0-1).
    anomaly_scores : np.ndarray
        Anomaly scores from an unsupervised model (0-1).
    alpha : float
        Weight for supervised probabilities.
    beta : float
        Weight for anomaly scores.

    Returns
    -------
    final_score : np.ndarray
        Final combined risk score.
    """
    p_supervised = np.asarray(p_supervised)
    anomaly_scores = np.asarray(anomaly_scores)

    if p_supervised.shape != anomaly_scores.shape:
        raise ValueError("p_supervised and anomaly_scores must have the same shape")

    # Normalize alpha and beta just in case
    s = alpha + beta
    if s <= 0:
        alpha_norm, beta_norm = 0.5, 0.5
    else:
        alpha_norm, beta_norm = alpha / s, beta / s

    final_score = alpha_norm * p_supervised + beta_norm * anomaly_scores
    return final_score
