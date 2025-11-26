from typing import Optional, Sequence

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder


def build_behavior_feature_table(
    df_raw: pd.DataFrame,
    target_column: str = "Revenue",
    drop_columns: Optional[Sequence[str]] = None,
    time_column: str = "date",
    user_column: str = "user",
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

    # Add simple temporal/user features if available
    if time_column in df.columns:
        ts = pd.to_datetime(df[time_column], errors="coerce")
        df["hour"] = ts.dt.hour
        df["dayofweek"] = ts.dt.dayofweek
        if user_column in df.columns:
            df = df.sort_values([user_column, time_column])
            df["events_per_user"] = df.groupby(user_column).cumcount()
            last_time = df.groupby(user_column)[time_column].shift(1)
            delta = (ts - pd.to_datetime(last_time, errors="coerce")).dt.total_seconds()
            df["secs_since_last"] = delta.fillna(delta.median() if np.isfinite(delta).any() else 0)
        df = df.drop(columns=[time_column])

    y = df[target_column].astype(int)
    X = df.drop(columns=[target_column])

    cat_cols = X.select_dtypes(include=["object", "bool", "category"]).columns.tolist()
    num_cols = X.select_dtypes(include=[np.number]).columns.tolist()

    print(f"Numeric features: {len(num_cols)}, Categorical features: {len(cat_cols)}")

    # Fill missing values before encoding
    X_enc = X.copy()
    if num_cols:
        X_enc[num_cols] = X_enc[num_cols].fillna(0)
    if cat_cols:
        X_enc[cat_cols] = X_enc[cat_cols].fillna("missing")
    for col in cat_cols:
        le = LabelEncoder()
        X_enc[col] = le.fit_transform(X_enc[col].astype(str))

    df_feats = X_enc.copy()
    df_feats[target_column] = y.values

    print("Behavior feature table shape:", df_feats.shape)
    return df_feats
