"""Train/validation/test splits."""
from typing import Dict, Tuple

import pandas as pd
from sklearn.model_selection import train_test_split


def split_train_val_test(
    df: pd.DataFrame,
    target: str,
    test_size: float = 0.2,
    val_size: float = 0.1,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    X = df.drop(columns=[target])
    y = df[target]

    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    val_fraction = val_size / (1 - test_size)
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=1 - val_fraction, random_state=random_state, stratify=y_temp
    )
    return X_train, X_val, X_test, y_train, y_val, y_test


__all__ = ["split_train_val_test"]
