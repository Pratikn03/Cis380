from typing import Optional, Sequence

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder


def build_behavior_feature_table(
    df_raw: pd.DataFrame,
    target_column: str = "Revenue",
    drop_columns: Optional[Sequence[str]] = None,
) -> pd.DataFrame:
    """
    Build a feature table for the Online Shoppers Intention dataset.

    - Target: `Revenue` (True/False -> 1/0)
    - Numeric columns kept as-is
    - Categorical/bool columns label-encoded
    """
    df = df_raw.copy()

    if target_column not in df.columns:
        raise KeyError(f"Target column '{target_column}' not found. Available: {df.columns.tolist()}")

    if drop_columns:
        for col in drop_columns:
            if col in df.columns:
                df.drop(columns=[col], inplace=True)

    y = df[target_column].astype(int)
    X = df.drop(columns=[target_column])

    cat_cols = X.select_dtypes(include=["object", "bool", "category"]).columns.tolist()
    num_cols = X.select_dtypes(include=[np.number]).columns.tolist()

    print(f"Numeric features: {len(num_cols)}, Categorical features: {len(cat_cols)}")

    X_enc = X.copy()
    for col in cat_cols:
        le = LabelEncoder()
        X_enc[col] = le.fit_transform(X_enc[col].astype(str))

    df_feats = X_enc.copy()
    df_feats[target_column] = y.values

    print("Behavior feature table shape:", df_feats.shape)
    return df_feats
