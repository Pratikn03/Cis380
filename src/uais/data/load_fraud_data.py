"""
Data loading utilities for fraud datasets (v1).

Assumptions:
- There is at least one CSV file in data/raw/fraud/.
- For v1, we assume a Kaggle-style fraud CSV with a binary target column,
  e.g. "Class" for the Credit Card Fraud dataset.
"""

from pathlib import Path
from typing import Optional

import pandas as pd


def find_default_fraud_csv() -> Path:
    """
    Locate a default fraud CSV file inside data/raw/fraud/.

    Returns
    -------
    path : Path
        Path to the first CSV file found.

    Raises
    ------
    FileNotFoundError
        If no CSV file is found in data/raw/fraud/.
    """
    project_root = Path(__file__).resolve().parents[3]
    fraud_dir = project_root / "data" / "raw" / "fraud"
    if not fraud_dir.exists():
        raise FileNotFoundError(f"Fraud raw data directory not found: {fraud_dir}")

    csv_files = list(fraud_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {fraud_dir}")
    return csv_files[0]


def load_fraud_data(csv_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the raw fraud dataset from CSV and return a pandas DataFrame.

    Parameters
    ----------
    csv_path : str, optional
        Optional explicit path to a CSV file. If None, the function will try
        to locate a CSV file inside data/raw/fraud/.

    Returns
    -------
    df : pandas.DataFrame
        Raw fraud data as loaded from disk (no feature engineering yet).
    """
    if csv_path is None:
        csv_path = find_default_fraud_csv()

    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Fraud CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    return df
