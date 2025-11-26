"""Dataset loaders for UAIS-V (fraud/cyber/behavior + NLP/Vision)."""
import pickle
from pathlib import Path
from typing import Tuple, List

import numpy as np
import pandas as pd

from uais.data.load_behavior_data import load_behavior_data as load_behavior_data_domain
from uais.data.load_cyber_data import load_cyber_data as load_cyber_data_domain
from uais.data.load_fraud_data import load_fraud_data as load_fraud_data_domain

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_RAW = PROJECT_ROOT / "data" / "raw"


def _load_all_tabular(path: Path) -> pd.DataFrame:
    """Load all CSV/Parquet files under a path (file or directory) and concatenate."""
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    if path.is_file():
        if path.suffix.lower() == ".parquet":
            return pd.read_parquet(path)
        return pd.read_csv(path)
    if not path.exists():
        raise FileNotFoundError(f"Path not found: {path}")
    files = sorted(list(path.rglob("*.csv")) + list(path.rglob("*.parquet")))
    if not files:
        raise FileNotFoundError(f"No CSV/Parquet files found under {path}")
    frames = []
    for f in files:
        if f.suffix.lower() == ".parquet":
            frames.append(pd.read_parquet(f))
        else:
            frames.append(pd.read_csv(f))
    return pd.concat(frames, ignore_index=True, sort=False)


# Existing domain loaders (now aggregate all files when given a directory)

def load_fraud_data(path: str | Path = "data/raw/fraud", n_rows: int | None = None, allow_synthetic: bool = True):
    df = load_fraud_data_domain(csv_path=path, n_rows=n_rows, allow_synthetic=allow_synthetic)
    print(f"✅ Loaded fraud data from {path} -> {df.shape}")
    return df


def load_cyber_data(path: str | Path = "data/raw/cyber", n_rows: int | None = None, allow_synthetic: bool = True):
    df = load_cyber_data_domain(raw_dir=path, n_rows=n_rows, allow_synthetic=allow_synthetic)
    print(f"✅ Loaded cyber data from {path} -> {df.shape}")
    return df


def load_behavior_data(path: str | Path = "data/raw/behavior", n_rows: int | None = None, allow_synthetic: bool = True):
    df = load_behavior_data_domain(csv_path=path, n_rows=n_rows, allow_synthetic=allow_synthetic)
    print(f"✅ Loaded behavior data from {path} -> {df.shape}")
    return df


def load_nlp_data(path: str | Path = "data/raw/nlp"):
    p = Path(path)
    df = _load_all_tabular(p)
    print(f"✅ Loaded NLP data from {p} -> {df.shape}")
    return df


def load_vision_data(path: str | Path = "data/raw/vision"):
    p = Path(path)
    # If pointing to images, this will fail; use CSV/Parquet metadata under vision if present.
    df = _load_all_tabular(p)
    print(f"✅ Loaded vision tabular data from {p} -> {df.shape}")
    return df


# Enron email loader

def load_enron_emails(subset: int | None = None, columns: list[str] | None = None) -> pd.DataFrame:
    csv_path = DATA_RAW / "nlp" / "enron_emails.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Enron CSV not found at {csv_path}. Run download_nlp_vision.py first.")
    df = pd.read_csv(csv_path)
    if columns is not None:
        existing = [c for c in columns if c in df.columns]
        df = df[existing]
    if subset is not None:
        df = df.iloc[:subset].copy()
    return df


# CIFAR-10 loader helpers

def _load_cifar_batch(batch_path: Path) -> Tuple[np.ndarray, np.ndarray]:
    with open(batch_path, "rb") as f:
        batch = pickle.load(f, encoding="latin1")
    data = batch["data"]
    labels = batch.get("labels") or batch.get("fine_labels") or batch.get("coarse_labels")
    images = data.reshape(-1, 3, 32, 32).astype("float32") / 255.0
    labels = np.array(labels, dtype="int64")
    return images, labels


def load_cifar10(split: str = "train") -> Tuple[np.ndarray, np.ndarray]:
    root = DATA_RAW / "vision" / "cifar-10-python"
    if not root.exists():
        raise FileNotFoundError(f"CIFAR-10 directory not found at {root}. Run download_nlp_vision.py first.")
    if split == "train":
        batch_files = [root / f"data_batch_{i}" for i in range(1, 6)]
    elif split == "test":
        batch_files = [root / "test_batch"]
    else:
        raise ValueError("split must be 'train' or 'test'")
    xs, ys = [], []
    for bf in batch_files:
        if not bf.exists():
            raise FileNotFoundError(f"Missing batch file: {bf}")
        Xb, yb = _load_cifar_batch(bf)
        xs.append(Xb)
        ys.append(yb)
    X = np.concatenate(xs, axis=0)
    y = np.concatenate(ys, axis=0)
    return X, y


if __name__ == "__main__":  # pragma: no cover
    print("Checking Enron...")
    try:
        df_enron = load_enron_emails(subset=5)
        print(df_enron.head())
    except Exception as e:
        print("Enron load failed:", e)

    print("\nChecking CIFAR-10...")
    try:
        X_train, y_train = load_cifar10("train")
        print("CIFAR-10 train:", X_train.shape, y_train.shape)
    except Exception as e:
        print("CIFAR load failed:", e)
