"""
Utilities to load CERT Insider Threat behavior logs
(e.g., logon.csv, http.csv, file.csv, email.csv, device.csv).

Start simple: focus on logon.csv first because it’s directly behavioral and good for anomaly/sequence work.
"""

from pathlib import Path
from typing import Optional, Union

import pandas as pd


def get_cert_raw_dir(base_dir: Optional[Union[str, Path]] = None) -> Path:
    """Return the directory where CERT raw CSVs are stored."""
    if base_dir is None:
        project_root = Path(__file__).resolve().parents[3]
        base_dir = project_root / "data" / "raw" / "behavior" / "cert"

    base_dir = Path(base_dir)
    if not base_dir.exists():
        raise FileNotFoundError(
            f"CERT raw directory not found: {base_dir}. Expected path: project_root/data/raw/behavior/cert"
        )
    return base_dir


def load_cert_logon(
    base_dir: Optional[Union[str, Path]] = None,
    n_rows: Optional[int] = None,
) -> pd.DataFrame:
    """Load the CERT logon.csv file (user login behavior)."""
    raw_dir = get_cert_raw_dir(base_dir)
    logon_path = raw_dir / "logon.csv"

    if not logon_path.exists():
        raise FileNotFoundError(
            f"logon.csv NOT found in {raw_dir}. Make sure you extracted CERT and placed logon.csv there."
        )

    print(f"Loading CERT logon data from: {logon_path}")
    df = pd.read_csv(logon_path)
    print("Full CERT logon shape:", df.shape)

    if n_rows is not None and n_rows < len(df):
        df = df.sample(n=n_rows, random_state=42).reset_index(drop=True)
        print(f"Subsampled CERT logon to {n_rows} rows.")

    return df


def load_cert_behavior_minimal(
    n_rows: Optional[int] = 50_000,
) -> pd.DataFrame:
    """Convenience wrapper: load a manageable subset of CERT logon behavior."""
    df_logon = load_cert_logon(n_rows=n_rows)
    return df_logon


__all__ = ["get_cert_raw_dir", "load_cert_logon", "load_cert_behavior_minimal"]
