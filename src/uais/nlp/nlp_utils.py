"""Utility helpers for NLP models (tokenization, batching, quick splits).

These are lightweight stubs to keep the repo structure consistent. Replace
or extend with your preferred preprocessing/tokenization utilities.
"""

from __future__ import annotations

from typing import List, Tuple

import pandas as pd
from sklearn.model_selection import train_test_split


def simple_train_val_split(texts: List[str], labels: List[int], test_size: float = 0.2, seed: int = 42) -> Tuple:
    """Small helper to split text/labels into train/val.

    This keeps an explicit stub so downstream training scripts have a common
    import path even if you swap in a more sophisticated dataset loader later.
    """

    return train_test_split(texts, labels, test_size=test_size, random_state=seed, stratify=labels)


def load_csv_text_label(path: str, text_col: str = "text", label_col: str = "label") -> Tuple[list[str], list[int]]:
    df = pd.read_csv(path)
    if text_col not in df.columns or label_col not in df.columns:
        raise KeyError(f"Columns {text_col} and {label_col} are required. Found: {df.columns.tolist()}")
    return df[text_col].astype(str).tolist(), df[label_col].astype(int).tolist()


__all__ = ["simple_train_val_split", "load_csv_text_label"]
