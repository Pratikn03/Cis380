"""Time-based drift and stability checks."""
from typing import Dict

import pandas as pd


def rolling_mean_drift(series_a: pd.Series, series_b: pd.Series, window: int = 24) -> Dict[str, float]:
    a_roll = series_a.rolling(window=window, min_periods=1).mean()
    b_roll = series_b.rolling(window=window, min_periods=1).mean()
    diff = (a_roll - b_roll).abs()
    return {
        "mean_abs_diff": float(diff.mean()),
        "max_abs_diff": float(diff.max()),
    }


__all__ = ["rolling_mean_drift"]
