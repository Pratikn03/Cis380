"""Convenience loaders for processed/raw datasets used by UAIS-V."""
from pathlib import Path
from typing import Optional

import pandas as pd

from ..paths import PROCESSED_DIR, RAW_DIR


def _read_table(path: Path, n_rows: Optional[int] = None) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path, nrows=n_rows)


def _first_existing(candidates: list[Path]) -> Optional[Path]:
    for p in candidates:
        if p and p.exists():
            return p
    return None


def load_fraud_features(path: Optional[Path] = None) -> pd.DataFrame:
    candidates = [
        path,
        PROCESSED_DIR / "fraud" / "fraud_features.parquet",
        RAW_DIR / "fraud" / "creditcard.csv",
    ]
    chosen = _first_existing(candidates)
    if not chosen:
        raise FileNotFoundError("Could not find fraud feature table or raw CSV.")
    return _read_table(chosen)


def load_cyber_features(path: Optional[Path] = None, n_rows: Optional[int] = None) -> pd.DataFrame:
    candidates = [
        path,
        PROCESSED_DIR / "cyber" / "unsw_nb15_features.parquet",
        RAW_DIR / "cyber" / "UNSW-NB15.csv",
    ]
    chosen = _first_existing(candidates)
    if not chosen:
        raise FileNotFoundError("Could not find cyber feature table.")
    return _read_table(chosen, n_rows)


def load_behavior_events(path: Optional[Path] = None, n_rows: Optional[int] = None) -> pd.DataFrame:
    candidates = [
        path,
        PROCESSED_DIR / "behavior" / "r4_2_raw.parquet",
        RAW_DIR / "behavior" / "online_shoppers_intention.csv",
    ]
    chosen = _first_existing(candidates)
    if not chosen:
        raise FileNotFoundError("Could not find behavior event log (CERT or online shoppers).")
    return _read_table(chosen, n_rows)


def load_labels(path: Optional[Path] = None) -> pd.Series:
    candidates = [path, PROCESSED_DIR / "labels.npy"]
    chosen = _first_existing(candidates)
    if not chosen:
        raise FileNotFoundError("Could not find labels.npy; provide a path explicitly.")
    import numpy as np

    return pd.Series(np.load(chosen))


__all__ = [
    "load_fraud_features",
    "load_cyber_features",
    "load_behavior_events",
    "load_labels",
]
