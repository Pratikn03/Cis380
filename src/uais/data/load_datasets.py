"""Dataset loaders for UAIS-V (fraud/cyber/behavior + NLP/Vision)."""
import os
import pickle
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_RAW = PROJECT_ROOT / "data" / "raw"


# Existing domain loaders

def load_fraud_data(path: str | Path = "data/raw/fraud/creditcard.csv"):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Fraud dataset not found: {p}")
    print(f"✅ Loading fraud dataset: {p}")
    return pd.read_csv(p)


def load_cyber_data(path: str | Path = "data/raw/cyber/UNSW-NB15.csv"):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Cyber dataset not found: {p}")
    print(f"✅ Loading cyber dataset: {p}")
    return pd.read_csv(p)


def load_behavior_data(path: str | Path = "data/raw/behavior/r4.2/logon.csv"):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Behavior dataset not found: {p}")
    print(f"✅ Loading CERT behavior dataset: {p}")
    return pd.read_csv(p)


def load_nlp_data(path: str | Path = "data/raw/nlp/enron_emails.csv"):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"NLP dataset not found: {p}")
    print(f"✅ Loading NLP dataset: {p}")
    return pd.read_csv(p)


def load_vision_data(path: str | Path = "data/raw/vision/deepfake_real.csv"):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Vision dataset not found: {p}")
    print(f"✅ Loading Vision dataset: {p}")
    return pd.read_csv(p)


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
