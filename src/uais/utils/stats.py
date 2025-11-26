"""Simple statistical utilities for CI and significance tests."""
from __future__ import annotations

from typing import Callable, Tuple

import numpy as np
from scipy import stats


def bootstrap_ci(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    metric_fn: Callable[[np.ndarray, np.ndarray], float],
    n_bootstrap: int = 200,
    alpha: float = 0.05,
    random_state: int = 42,
) -> Tuple[float, float]:
    """Compute bootstrap confidence interval for a metric.

    Returns (lower, upper) bounds.
    """
    rng = np.random.default_rng(random_state)
    n = len(y_true)
    scores = []
    for _ in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        scores.append(metric_fn(y_true[idx], y_prob[idx]))
    lower = float(np.percentile(scores, 100 * alpha / 2))
    upper = float(np.percentile(scores, 100 * (1 - alpha / 2)))
    return lower, upper


def paired_ttest(a: np.ndarray, b: np.ndarray) -> float:
    """Return p-value of paired t-test between two score arrays."""
    _, p = stats.ttest_rel(a, b, nan_policy="omit")
    return float(p)


def wilcoxon_test(a: np.ndarray, b: np.ndarray) -> float:
    """Return p-value of Wilcoxon signed-rank test between two score arrays."""
    try:
        _, p = stats.wilcoxon(a, b)
    except ValueError:
        p = np.nan
    return float(p)


__all__ = ["bootstrap_ci", "paired_ttest", "wilcoxon_test"]
