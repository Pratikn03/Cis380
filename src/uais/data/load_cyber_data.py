from pathlib import Path
from typing import Optional, Union, List

import pandas as pd


def _find_cyber_csvs(raw_dir: Path) -> List[Path]:
    if not raw_dir.exists():
        raise FileNotFoundError(f"Cyber raw directory not found: {raw_dir}")
    csv_files = sorted(raw_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {raw_dir}")
    return csv_files


def load_cyber_data(
    raw_dir: Optional[Union[str, Path]] = None,
    n_rows: Optional[int] = None,
) -> pd.DataFrame:
    """
    Load the UNSW-NB15 cyber intrusion dataset from data/raw/cyber.
    """
    if raw_dir is None:
        project_root = Path(__file__).resolve().parents[3]
        raw_dir = project_root / "data" / "raw" / "cyber"
    else:
        raw_dir = Path(raw_dir)

    csv_files = _find_cyber_csvs(raw_dir)
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

    if n_rows is not None and n_rows < len(df_all):
        df_all = df_all.sample(n=n_rows, random_state=42).reset_index(drop=True)
        print(f"Subsampled to {n_rows} rows.")

    return df_all
