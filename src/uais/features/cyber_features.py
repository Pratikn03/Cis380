from typing import Optional, Sequence

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder


def build_cyber_feature_table(
    df_raw: pd.DataFrame,
    target_column: str = "label",
    drop_columns: Optional[Sequence[str]] = None,
    freq_encode_cats: bool = True,
) -> pd.DataFrame:
    """Build a feature table for UNSW-NB15.

    - Numeric columns kept as-is
    - Categorical columns label-encoded
    - Target coerced to integer (drops rows with missing or infinite target)
    """
    df = df_raw.copy()

    if target_column not in df.columns:
        raise KeyError(f"Target column '{target_column}' not found. Available: {df.columns.tolist()}")

    if drop_columns:
        for col in drop_columns:
            if col in df.columns:
                df.drop(columns=[col], inplace=True)

    target_series = df[target_column]
    if not np.issubdtype(target_series.dtype, np.number):
        target_series = pd.Series(LabelEncoder().fit_transform(target_series.astype(str)), index=df.index)
    target_series = pd.to_numeric(target_series, errors="coerce")
    target_series = target_series.replace([np.inf, -np.inf], np.nan)
    df[target_column] = target_series
    df = df[np.isfinite(df[target_column])]
    df = df.dropna(subset=[target_column])
    y = df[target_column].astype(int)

    X = df.drop(columns=[target_column])
    cat_cols = X.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
    num_cols = X.select_dtypes(include=[np.number]).columns.tolist()

    # Basic rate features if bytes/duration available
    if all(col in X.columns for col in ["dur", "sbytes", "dbytes"]):
        dur = pd.to_numeric(X["dur"], errors="coerce").replace([np.inf, -np.inf], np.nan)
        dur = dur.where(dur > 0, np.nan)
        X["bytes_per_sec_src"] = X["sbytes"] / dur
        X["bytes_per_sec_dst"] = X["dbytes"] / dur
        num_cols.extend(["bytes_per_sec_src", "bytes_per_sec_dst"])

    # Frequency encoding for categoricals to capture rarity
    if freq_encode_cats and cat_cols:
        for col in cat_cols:
            freq = X[col].value_counts(normalize=True)
            X[f"{col}_freq"] = X[col].map(freq).fillna(0)
            num_cols.append(f"{col}_freq")

    print(f"Numeric features: {len(num_cols)}, Categorical features: {len(cat_cols)}")

    X_enc = X.copy()
    for col in cat_cols:
        le = LabelEncoder()
        X_enc[col] = le.fit_transform(X_enc[col].astype(str))

    df_feats = X_enc.copy()
    df_feats[target_column] = y.values

    print("Cyber feature table shape:", df_feats.shape)
    return df_feats
