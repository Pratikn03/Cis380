"""
Feature engineering for fraud detection (v1).

This version is designed to work with the Kaggle Credit Card Fraud dataset:
- Columns: Time, V1...V28, Amount, Class
- Time is seconds elapsed between each transaction and the first transaction.
"""

from typing import Optional

import numpy as np
import pandas as pd


def add_basic_fraud_features(
    df: pd.DataFrame,
    time_column: str = "Time",
    amount_column: str = "Amount",
    copy: bool = True,
) -> pd.DataFrame:
    """
    Add basic features: log(amount), simple time-based features.

    Parameters
    ----------
    df : pandas.DataFrame
        Raw fraud dataframe.
    time_column : str
        Name of the time column (e.g., 'Time').
    amount_column : str
        Name of the transaction amount column.
    copy : bool
        Whether to operate on a copy of df (recommended).

    Returns
    -------
    df_feats : pandas.DataFrame
        DataFrame with additional feature columns.
    """
    if copy:
        df_feats = df.copy()
    else:
        df_feats = df

    # Log-transformed amount to reduce skew
    if amount_column in df_feats.columns:
        df_feats["amount_log"] = np.log1p(df_feats[amount_column])
    else:
        raise KeyError(f"{amount_column} column not found in DataFrame")

    # Time-based features (specific to the Kaggle fraud dataset)
    if time_column in df_feats.columns:
        # Time is in seconds from first transaction
        df_feats["time_hours"] = df_feats[time_column] / 3600.0
        # Map to hour-of-day assuming day length of 24h
        seconds_per_day = 24 * 3600
        df_feats["time_seconds_mod_day"] = df_feats[time_column] % seconds_per_day
        df_feats["hour_of_day"] = (df_feats["time_seconds_mod_day"] / 3600.0).astype(int)
    else:
        raise KeyError(f"{time_column} column not found in DataFrame")

    return df_feats


def build_fraud_feature_table(
    df: pd.DataFrame,
    time_column: str = "Time",
    amount_column: str = "Amount",
    target_column: str = "Class",
    drop_original_time: bool = False,
) -> pd.DataFrame:
    """
    Full feature pipeline entrypoint for fraud (v1).

    Steps:
    1. Add basic features (log amount, time-based).
    2. Optionally drop raw Time column.
    3. Return final feature table.

    Parameters
    ----------
    df : pandas.DataFrame
        Raw fraud DataFrame.
    time_column : str
        Name of the time column.
    amount_column : str
        Name of the amount column.
    target_column : str
        Name of the target label column (0/1).
    drop_original_time : bool
        Whether to drop the original time column after feature creation.

    Returns
    -------
    df_features : pandas.DataFrame
        Feature-engineered table ready for modeling, including the target column.
    """
    df_feats = add_basic_fraud_features(df, time_column=time_column, amount_column=amount_column, copy=True)

    if drop_original_time and time_column in df_feats.columns:
        df_feats = df_feats.drop(columns=[time_column])

    # Ensure target column is present
    if target_column not in df_feats.columns:
        raise KeyError(f"Target column '{target_column}' not found in DataFrame")

    return df_feats
