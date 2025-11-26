from pathlib import Path
from typing import Optional, Union

import numpy as np
import pandas as pd


def _synthetic_behavior(n_rows: int = 200) -> pd.DataFrame:
    """Fallback synthetic Online Shoppers-style dataset."""
    rng = np.random.default_rng(42)
    n = n_rows
    df = pd.DataFrame(
        {
            "Administrative": rng.integers(0, 5, size=n),
            "Administrative_Duration": rng.gamma(2.0, 10.0, size=n),
            "Informational": rng.integers(0, 3, size=n),
            "Informational_Duration": rng.gamma(1.5, 5.0, size=n),
            "ProductRelated": rng.integers(1, 10, size=n),
            "ProductRelated_Duration": rng.gamma(3.0, 15.0, size=n),
            "BounceRates": rng.uniform(0, 0.2, size=n),
            "ExitRates": rng.uniform(0, 0.3, size=n),
            "PageValues": rng.uniform(0, 10, size=n),
            "SpecialDay": rng.uniform(0, 1, size=n),
            "Month": rng.choice(list(range(1, 13)), size=n),
            "OperatingSystems": rng.choice(list(range(1, 7)), size=n),
            "Browser": rng.choice(list(range(1, 11)), size=n),
            "Region": rng.choice(list(range(1, 10)), size=n),
            "TrafficType": rng.choice(list(range(1, 21)), size=n),
            "VisitorType": rng.choice(["Returning_Visitor", "New_Visitor"], size=n),
            "Weekend": rng.choice([False, True], size=n),
            "Revenue": rng.binomial(1, 0.15, size=n),
        }
    )
    return df


def _load_ldap_dir(ldap_dir: Path) -> pd.DataFrame:
    """Load all LDAP CSVs (CERT r4.2) and add a placeholder target."""
    csv_files = sorted(ldap_dir.rglob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {ldap_dir}")
    frames = [pd.read_csv(f) for f in csv_files]
    df = pd.concat(frames, ignore_index=True)
    # Standardize user column name for downstream features if present
    if "user_id" in df.columns and "user" not in df.columns:
        df = df.rename(columns={"user_id": "user"})
    # Placeholder target for unsupervised flows
    df["Revenue"] = 0
    return df


def load_behavior_data(
    csv_path: Optional[Union[str, Path]] = None,
    n_rows: Optional[int] = None,
    allow_synthetic: bool = True,
) -> pd.DataFrame:
    """
    Load behavior data.

    Priority:
    1) If csv_path is provided (file or directory), use that.
    2) If CERT r4.2 LDAP directory exists, load all CSVs there.
    3) Fallback to Online Shoppers Intention CSV.
    """
    project_root = Path(__file__).resolve().parents[3]
    ldap_dir = project_root / "data" / "raw" / "behavior" / "r4.2" / "LDAP"
    default_csv = project_root / "data" / "raw" / "behavior" / "online_shoppers_intention.csv"

    # Allow passing config dicts (from load_config) to derive a path if present
    if isinstance(csv_path, dict):
        data_cfg = csv_path.get("data", csv_path)
        candidate = data_cfg.get("path") or data_cfg.get("file_name")
        csv_path = candidate if candidate else None

    source = csv_path
    if source is None:
        if ldap_dir.exists():
            source = ldap_dir
        else:
            source = default_csv

    source_path = Path(source)
    if not source_path.is_absolute():
        source_path = project_root / source_path
    if source_path.is_dir():
        df = _load_ldap_dir(source_path)
        print(f"Loaded LDAP behavior directory: {source_path} -> shape {df.shape}")
    else:
        if not source_path.exists():
            if csv_path is None and allow_synthetic:
                print(f"[warn] Behavior data not found at {source_path}; using synthetic sample.")
                df = _synthetic_behavior(n_rows or 500)
            else:
                raise FileNotFoundError(f"Behavior data not found: {source_path}")
        else:
            if source_path.suffix.lower() == ".parquet":
                df = pd.read_parquet(source_path)
            else:
                df = pd.read_csv(source_path)
            print(f"Loaded behavior data from {source_path}, shape {df.shape}")
            if "Revenue" not in df.columns:
                df["Revenue"] = 0  # best-effort placeholder for unlabeled data

    # Basic cleaning: coerce target to numeric and drop rows with non-finite target
    if "Revenue" in df.columns:
        df["Revenue"] = pd.to_numeric(df["Revenue"], errors="coerce")
        before = len(df)
        df = df[np.isfinite(df["Revenue"])]
        if len(df) != before:
            print(f"Dropped {before - len(df)} rows with non-finite target")
        df["Revenue"] = df["Revenue"].fillna(0).astype(int)
    # Fill missing for object columns to avoid LabelEncoder blow-ups downstream
    obj_cols = df.select_dtypes(include=["object", "category"]).columns
    if len(obj_cols) > 0:
        df[obj_cols] = df[obj_cols].fillna("missing")

    if n_rows is not None and n_rows < len(df):
        df = df.sample(n=n_rows, random_state=42).reset_index(drop=True)
        print(f"Subsampled to {n_rows} rows.")

    return df
