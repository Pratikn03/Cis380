"""Tabular drift detection utilities."""
from typing import Dict, List

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp


def ks_drift(base: pd.DataFrame, new: pd.DataFrame, numeric_cols: List[str]) -> Dict[str, float]:
    results: Dict[str, float] = {}
    for col in numeric_cols:
        if col not in base.columns or col not in new.columns:
            continue
        stat, pvalue = ks_2samp(base[col].dropna(), new[col].dropna())
        results[col] = pvalue
    return results


__all__ = ["ks_drift"]
