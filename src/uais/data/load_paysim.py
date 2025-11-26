import shutil
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Union

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PATH = PROJECT_ROOT / "data" / "raw" / "fraud" / "paysim" / "paysim_transactions.csv"


def _ensure_paysim(path: Path) -> Path:
    """Ensure PaySim CSV exists; download via kagglehub if available."""
    if path.exists():
        return path
    try:
        import kagglehub  # type: ignore
    except Exception as exc:
        raise FileNotFoundError(
            f"PaySim CSV not found at {path}. Install kagglehub and ensure Kaggle credentials to auto-download."
        ) from exc

    print("[info] Downloading PaySim via kagglehub: ealaxi/paysim1 ...")
    download_dir = Path(kagglehub.dataset_download("ealaxi/paysim1"))
    candidates = list(download_dir.rglob("PS_20174392719_1491204439457_log.csv"))
    if not candidates:
        candidates = list(download_dir.rglob("*.csv"))
    if not candidates:
        raise FileNotFoundError(f"No CSV found under downloaded path: {download_dir}")

    src = candidates[0]
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, path)
    print(f"[ok] PaySim copied to {path}")
    return path


def _synthetic_paysim(n_rows: int = 1000) -> pd.DataFrame:
    """Synthetic PaySim-like dataset for CI/demos."""
    rng = np.random.default_rng(42)
    n = n_rows
    df = pd.DataFrame(
        {
            "step": rng.integers(0, 500, size=n),
            "type": rng.choice(["PAYMENT", "TRANSFER", "CASH_OUT"], size=n),
            "amount": rng.gamma(2.0, 500.0, size=n),
            "oldbalanceOrg": rng.gamma(2.0, 1000.0, size=n),
            "newbalanceOrg": rng.gamma(2.0, 1000.0, size=n),
            "oldbalanceDest": rng.gamma(2.0, 1000.0, size=n),
            "newbalanceDest": rng.gamma(2.0, 1000.0, size=n),
            "isFraud": rng.binomial(1, 0.03, size=n),
            "isFlaggedFraud": rng.binomial(1, 0.005, size=n),
        }
    )
    return df


def load_paysim(
    n_rows: Optional[int] = None,
    path: Optional[Union[str, Path]] = None,
    allow_synthetic: bool = True,
) -> pd.DataFrame:
    """
    Load the PaySim mobile money fraud dataset, auto-downloading via kagglehub if missing.

    Parameters
    ----------
    n_rows : int or None
        If set, load only the first n_rows (useful for debugging).
    path : optional override path to the CSV.
    """
    target = Path(path) if path else DEFAULT_PATH
    if not target.is_absolute():
        target = PROJECT_ROOT / target

    try:
        target = _ensure_paysim(target)
        df = pd.read_csv(target, nrows=n_rows)
    except Exception as exc:
        if allow_synthetic:
            print(f"[warn] PaySim not available ({exc}); using synthetic sample.")
            df = _synthetic_paysim(n_rows or 1000)
        else:
            raise
    df.columns = [c.strip().lower() for c in df.columns]
    return df


if __name__ == "__main__":
    df = load_paysim(5_000)
    print(df.head())
    print(df["isfraud"].value_counts(normalize=True))
