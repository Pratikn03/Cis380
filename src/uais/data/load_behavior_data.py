from pathlib import Path
from typing import Optional, Union

import pandas as pd


def load_behavior_data(
    csv_path: Optional[Union[str, Path]] = None,
    n_rows: Optional[int] = None,
) -> pd.DataFrame:
    """
    Load the Online Shoppers Intention (behavior) dataset.

    Parameters
    ----------
    csv_path : str or Path, optional
        Path to the main CSV file. If None, defaults to
        project_root/data/raw/behavior/online_shoppers_intention.csv.
    n_rows : int, optional
        If given, sample this many rows.

    Returns
    -------
    DataFrame
        Behavior dataset.
    """
    if csv_path is None:
        project_root = Path(__file__).resolve().parents[3]
        csv_path = project_root / "data" / "raw" / "behavior" / "online_shoppers_intention.csv"

    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Behavior CSV not found: {csv_path}")

    print(f"Loading behavior data from {csv_path}")
    df = pd.read_csv(csv_path)
    print("Behavior raw shape:", df.shape)

    if n_rows is not None and n_rows < len(df):
        df = df.sample(n=n_rows, random_state=42).reset_index(drop=True)
        print(f"Subsampled to {n_rows} rows.")

    return df
