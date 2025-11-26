"""
Data loading utilities for fraud datasets (v1).

Assumptions:
- There is at least one CSV file in data/raw/fraud/.
- For v1, we assume a Kaggle-style fraud CSV with a binary target column,
  e.g. "Class" for the Credit Card Fraud dataset.
"""

from pathlib import Path
from typing import Optional, List, Union

import numpy as np
import pandas as pd
from .load_paysim import load_paysim


def _synthetic_fraud(n_rows: int = 1000) -> pd.DataFrame:
    """Credit-card style synthetic dataset for smoke tests."""
    rng = np.random.default_rng(42)
    n = n_rows
    data = {
        "Time": rng.integers(0, 100000, size=n),
        "Amount": rng.gamma(2.0, 50.0, size=n),
        "Class": rng.binomial(1, 0.02, size=n),
    }
    for i in range(1, 29):
        data[f"V{i}"] = rng.normal(0, 1, size=n)
    return pd.DataFrame(data)


def _normalize_fraud_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Align common fraud column names (case-insensitive) for downstream pipelines."""
    lower_map = {c.lower(): c for c in df.columns}
    if "class" in lower_map and "Class" not in df.columns:
        df = df.rename(columns={lower_map["class"]: "Class"})
    if "isfraud" in lower_map and "Class" not in df.columns:
        df = df.rename(columns={lower_map["isfraud"]: "Class"})
    if "time" in lower_map and "Time" not in df.columns:
        df = df.rename(columns={lower_map["time"]: "Time"})
    if "amount" in lower_map and "Amount" not in df.columns:
        df = df.rename(columns={lower_map["amount"]: "Amount"})
    if "Class" in df.columns:
        df["Class"] = pd.to_numeric(df["Class"], errors="coerce").fillna(0).astype(int)
    return df


def _find_all_fraud_files(root: Path) -> List[Path]:
    """Find all CSV/Parquet files under fraud raw directory."""
    if not root.exists():
        raise FileNotFoundError(f"Fraud raw data directory not found: {root}")
    files = sorted(list(root.rglob("*.csv")) + list(root.rglob("*.parquet")))
    if not files:
        raise FileNotFoundError(f"No CSV/Parquet files found under {root}")
    return files


def load_fraud_data(
    csv_path: Optional[Union[str, Path, dict]] = None,
    n_rows: Optional[int] = None,
    allow_synthetic: bool = True,
    prefer: Optional[str] = None,
) -> pd.DataFrame:
    """
    Load fraud data. If a directory is provided (or omitted), load and concatenate all CSV/Parquet files under it.

    Parameters
    ----------
    csv_path : optional path or config dict
        Directory or file to load. If None, uses data/raw/fraud.
    n_rows : optional int
        Deterministic subsample size.
    allow_synthetic : bool
        If True, return a synthetic credit-card style dataset when no files are found.
    prefer : str, optional
        If provided, prefer "creditcard" or "paysim" datasets when both are present.
    """
    project_root = Path(__file__).resolve().parents[3]
    if isinstance(csv_path, dict):
        data_cfg = csv_path.get("data", csv_path)
        csv_path = data_cfg.get("path") or data_cfg.get("file_name")

    if csv_path is None:
        csv_path = project_root / "data" / "raw" / "fraud"

    path = Path(csv_path)
    if not path.is_absolute():
        path = project_root / path

    prefer = prefer.lower() if isinstance(prefer, str) else None

    if path.is_dir():
        frames = []

        # PaySim (auto-download if available)
        paysim_csv = path / "paysim" / "paysim_transactions.csv"
        if prefer in (None, "paysim"):
            try:
                frames.append(_normalize_fraud_frame(load_paysim(n_rows=n_rows, path=paysim_csv, allow_synthetic=allow_synthetic)))
            except FileNotFoundError as exc:
                print(f"[warn] PaySim not available: {exc}")

        # Creditcard dataset if present
        creditcard_csv = path / "creditcard.csv"
        if prefer in (None, "creditcard") and creditcard_csv.exists():
            frames.append(_normalize_fraud_frame(load_creditcard(n_rows, allow_synthetic=allow_synthetic)))

        try:
            files = _find_all_fraud_files(path)
        except FileNotFoundError as exc:
            files = []
            if not frames and allow_synthetic and csv_path is None:
                print(f"[warn] {exc}. Falling back to synthetic fraud sample.")
                return _synthetic_fraud(n_rows or 1000)
            if not frames:
                raise

        for f in files:
            if f in {paysim_csv, creditcard_csv}:
                continue
            if f.suffix.lower() == ".parquet":
                df = pd.read_parquet(f)
            else:
                df = pd.read_csv(f)
            df = _normalize_fraud_frame(df)
            if "Class" not in df.columns:
                print(f"[warn] Skipping {f} (no fraud label column).")
                continue
            frames.append(df)

        if not frames:
            if allow_synthetic and csv_path is None:
                print("[warn] No usable fraud data found; using synthetic fallback.")
                return _synthetic_fraud(n_rows or 1000)
            raise FileNotFoundError(f"No fraud CSV/Parquet files found under {path}")

        df = pd.concat(frames, ignore_index=True, sort=False)

    else:
        if not path.exists():
            if csv_path is None and allow_synthetic:
                print(f"[warn] Fraud data not found at {path}; using synthetic sample.")
                return _synthetic_fraud(n_rows or 1000)
            raise FileNotFoundError(f"Fraud data not found: {path}")

        if path.suffix.lower() == ".parquet":
            df = pd.read_parquet(path)
        else:
            df = pd.read_csv(path)
        df = _normalize_fraud_frame(df)

    if n_rows is not None and len(df) > n_rows:
        df = df.sample(n=n_rows, random_state=42).reset_index(drop=True)
        print(f"Subsampled to {n_rows} rows.")

    return df


def load_creditcard(n_rows: Optional[int] = None, allow_synthetic: bool = True) -> pd.DataFrame:
    """Load the Credit Card Fraud dataset (default path: data/raw/fraud/creditcard.csv)."""
    project_root = Path(__file__).resolve().parents[3]
    path = project_root / "data" / "raw" / "fraud" / "creditcard.csv"
    if not path.exists():
        if allow_synthetic:
            print(f"[warn] Creditcard CSV not found at {path}; using synthetic fallback.")
            return _synthetic_fraud(n_rows or 1000)
        raise FileNotFoundError(f"Creditcard CSV not found at {path}")
    return pd.read_csv(path, nrows=n_rows)


def get_fraud_datasets(n_rows: Optional[int] = None) -> dict:
    """Convenience helper to load key fraud datasets (creditcard + paysim)."""
    return {
        "creditcard": load_creditcard(n_rows),
        "paysim": load_paysim(n_rows),
    }
