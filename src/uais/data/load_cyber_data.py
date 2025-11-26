from pathlib import Path
from typing import Optional, Union, List

import numpy as np
import pandas as pd


def _synthetic_cyber(n_rows: int = 500) -> pd.DataFrame:
    """Fallback UNSW-like synthetic dataset with mixed categorical/numeric fields."""
    rng = np.random.default_rng(42)
    n = n_rows
    df = pd.DataFrame(
        {
            "srcip": rng.choice([f"10.0.0.{i}" for i in range(1, 6)], size=n),
            "sport": rng.integers(1024, 20000, size=n),
            "dstip": rng.choice([f"172.16.0.{i}" for i in range(1, 6)], size=n),
            "dsport": rng.integers(80, 9000, size=n),
            "proto": rng.choice(["tcp", "udp", "icmp"], size=n),
            "service": rng.choice(["http", "ftp", "dns", "ssh"], size=n),
            "state": rng.choice(["CON", "FIN", "INT"], size=n),
            "dur": rng.exponential(0.5, size=n),
            "sbytes": rng.integers(200, 5000, size=n),
            "dbytes": rng.integers(200, 7000, size=n),
            "sttl": rng.integers(5, 64, size=n),
            "dttl": rng.integers(5, 64, size=n),
            "label": rng.binomial(1, 0.25, size=n),
        }
    )
    return df


def _normalize_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize label column name to `label` and coerce to int."""
    lower_map = {c.lower(): c for c in df.columns}
    target_col = None
    for cand in ("label", "class", "target"):
        if cand in lower_map:
            target_col = lower_map[cand]
            break
    if target_col is None and "attack_cat" in lower_map:
        attack_col = lower_map["attack_cat"]
        df["label"] = (df[attack_col].astype(str).str.lower() != "normal").astype(int)
    elif target_col is not None and target_col != "label":
        df = df.rename(columns={target_col: "label"})

    if "label" not in df.columns:
        raise KeyError(f"Target column not found in cyber data. Columns: {df.columns.tolist()}")

    df["label"] = pd.to_numeric(df["label"], errors="coerce").fillna(0)
    df["label"] = df["label"].replace([np.inf, -np.inf], np.nan).fillna(0).astype(int)
    return df


def _find_cyber_csvs(raw_dir: Path) -> List[Path]:
    if not raw_dir.exists():
        raise FileNotFoundError(f"Cyber raw directory not found: {raw_dir}")
    # Search recursively to pick up any split files
    csv_files = sorted(raw_dir.rglob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {raw_dir}")
    return csv_files


def load_cyber_data(
    raw_dir: Optional[Union[str, Path, dict]] = None,
    n_rows: Optional[int] = None,
    allow_synthetic: bool = True,
) -> pd.DataFrame:
    """
    Load the UNSW-NB15 cyber intrusion dataset by combining all CSVs under data/raw/cyber.

    If a config dict is provided, it will try to use data.path inside it.
    """
    project_root = Path(__file__).resolve().parents[3]
    if isinstance(raw_dir, dict):
        data_cfg = raw_dir.get("data", raw_dir)
        raw_dir = data_cfg.get("path")

    if raw_dir is None:
        raw_dir = project_root / "data" / "raw" / "cyber"
    else:
        raw_dir = Path(raw_dir)
        if not raw_dir.is_absolute():
            raw_dir = project_root / raw_dir

    if raw_dir.is_file():
        # Support loading a single CSV/parquet if explicitly passed
        if raw_dir.suffix.lower() == ".parquet":
            df_all = pd.read_parquet(raw_dir)
        else:
            df_all = pd.read_csv(raw_dir)
        print(f"Loaded cyber data from {raw_dir}, shape {df_all.shape}")
    else:
        try:
            csv_files = _find_cyber_csvs(raw_dir)
        except FileNotFoundError as exc:
            if raw_dir == project_root / "data" / "raw" / "cyber" and allow_synthetic:
                print(f"[warn] {exc}. Falling back to synthetic cyber data.")
                df_all = _synthetic_cyber(n_rows or 500)
                csv_files = []
            else:
                raise
        if csv_files:
            print(f"Found {len(csv_files)} cyber CSV file(s) in {raw_dir}")
            dfs = []
            for f in csv_files:
                print(f"Loading {f.name} ...")
                try:
                    df = pd.read_csv(f)
                except UnicodeDecodeError:
                    df = pd.read_csv(f, encoding="latin1")
                dfs.append(df)
            df_all = pd.concat(dfs, ignore_index=True)
            print("Full cyber raw shape:", df_all.shape)

    df_all.columns = [c.strip() for c in df_all.columns]
    try:
        df_all = _normalize_labels(df_all)
    except Exception as exc:
        if allow_synthetic and raw_dir == project_root / "data" / "raw" / "cyber":
            print(f"[warn] Label normalization failed ({exc}); using synthetic cyber sample.")
            df_all = _synthetic_cyber(n_rows or 500)
        else:
            raise

    if n_rows is not None and n_rows < len(df_all):
        df_all = df_all.sample(n=n_rows, random_state=42).reset_index(drop=True)
        print(f"Subsampled to {n_rows} rows.")

    return df_all
