from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd

_PATTERN_MULTIPLIERS: Dict[str, float] = {
    "duration": 4.0,
    "time": 4.0,
    "seconds": 4.0,
    "session": 4.0,
    "events": 5.0,
    "bytes": 6.0,
    "files": 6.0,
    "product": 3.0,
    "page": 3.0,
    "administrative": 3.0,
    "informational": 3.0,
    "traffic": 2.5,
    "exit": 2.0,
    "bounce": 2.0,
}


def _column_multiplier(name: str) -> float:
    lower = name.lower()
    mult = 1.0
    for key, value in _PATTERN_MULTIPLIERS.items():
        if key in lower:
            mult = max(mult, value)
    return mult


def _is_rate_feature(name: str) -> bool:
    lower = name.lower()
    return any(tag in lower for tag in ("rate", "ratio", "percent", "prob"))


def _safe_quantile(series: pd.Series, q: float) -> float:
    values = series.dropna().to_numpy()
    if values.size == 0:
        return 0.0
    return float(np.quantile(values.astype(float), q))


def augment_insider_patterns(
    df_features: pd.DataFrame,
    *,
    target_column: str,
    ratio: float = 0.05,
    seed: int = 42,
    max_rows: int | None = None,
) -> pd.DataFrame:
    """Add synthetic insider-like rows to a behavior feature table."""
    if ratio <= 0 or df_features.empty:
        return df_features

    rng = np.random.default_rng(seed)
    base = df_features.copy()
    num_cols = base.select_dtypes(include=[np.number]).columns.tolist()
    if target_column not in base.columns:
        raise KeyError(f"Target column '{target_column}' not present in features.")
    if target_column in num_cols:
        num_cols.remove(target_column)

    n_new = max(1, int(len(base) * ratio))
    if max_rows is not None:
        n_new = min(n_new, int(max_rows))

    sample = base.sample(n=n_new, replace=True, random_state=seed).copy()
    for col in num_cols:
        series = base[col]
        mult = _column_multiplier(col)
        high = _safe_quantile(series, 0.95)
        std = float(np.std(series.astype(float))) if np.isfinite(series).any() else 0.0
        noise = rng.normal(0.0, std if std > 0 else 1.0, size=n_new)

        if _is_rate_feature(col):
            sample[col] = np.clip(high * 1.5 + noise * 0.1, 0.0, 1.0)
        elif mult > 1.0:
            sample[col] = high * mult + noise
        else:
            sample[col] = high + abs(noise)

        if series.min(skipna=True) >= 0:
            sample[col] = np.clip(sample[col], 0.0, None)

    # Mark insider rows as positive/anomalous target.
    sample[target_column] = 1
    return pd.concat([base, sample], ignore_index=True)


def insider_summary(df_features: pd.DataFrame, *, target_column: str) -> dict[str, float]:
    if df_features.empty or target_column not in df_features.columns:
        return {}
    values = df_features[target_column]
    return {
        "rows": float(len(df_features)),
        "positives": float((values == 1).sum()),
        "positive_ratio": float((values == 1).mean()) if len(values) else 0.0,
    }


__all__ = ["augment_insider_patterns", "insider_summary"]
