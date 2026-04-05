"""Shared confidence/calibration utilities for training and serving flows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class ConfidenceSummary:
    ece: float
    brier_score: float
    mean_confidence: float
    mean_correctness: float
    n_samples: int


def apply_temperature_scaling(probs: np.ndarray, temperature: float) -> np.ndarray:
    """Calibrate binary probabilities with a temperature scalar."""
    temperature = max(1e-6, float(temperature))
    clipped = np.clip(probs.astype(np.float64), 1e-8, 1.0 - 1e-8)
    logits = np.log(clipped / (1.0 - clipped))
    scaled = logits / temperature
    return 1.0 / (1.0 + np.exp(-scaled))


def expected_calibration_error(
    y_true: Iterable[int],
    y_prob: Iterable[float],
    *,
    n_bins: int = 15,
) -> float:
    y_true_arr = np.asarray(list(y_true), dtype=np.int64)
    y_prob_arr = np.asarray(list(y_prob), dtype=np.float64)
    if y_true_arr.size == 0:
        return 0.0

    bins = np.linspace(0.0, 1.0, max(2, int(n_bins)) + 1)
    ece = 0.0
    total = float(y_true_arr.size)
    for i in range(len(bins) - 1):
        low, high = bins[i], bins[i + 1]
        if i == len(bins) - 2:
            mask = (y_prob_arr >= low) & (y_prob_arr <= high)
        else:
            mask = (y_prob_arr >= low) & (y_prob_arr < high)
        if not np.any(mask):
            continue
        acc = float(np.mean(y_true_arr[mask]))
        conf = float(np.mean(y_prob_arr[mask]))
        ece += (float(np.sum(mask)) / total) * abs(acc - conf)
    return float(ece)


def confidence_summary(
    y_true: Iterable[int],
    y_prob: Iterable[float],
    *,
    n_bins: int = 15,
) -> ConfidenceSummary:
    y_true_arr = np.asarray(list(y_true), dtype=np.int64)
    y_prob_arr = np.asarray(list(y_prob), dtype=np.float64)
    if y_true_arr.size == 0:
        return ConfidenceSummary(
            ece=0.0,
            brier_score=0.0,
            mean_confidence=0.0,
            mean_correctness=0.0,
            n_samples=0,
        )

    ece = expected_calibration_error(y_true_arr, y_prob_arr, n_bins=n_bins)
    brier = float(np.mean((y_prob_arr - y_true_arr) ** 2))
    mean_conf = float(np.mean(y_prob_arr))
    mean_correct = float(np.mean(y_true_arr))
    return ConfidenceSummary(
        ece=ece,
        brier_score=brier,
        mean_confidence=mean_conf,
        mean_correctness=mean_correct,
        n_samples=int(y_true_arr.size),
    )
