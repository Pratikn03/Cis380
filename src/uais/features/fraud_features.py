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

    # Amount column fallback (creditcard uses 'Amount', PaySim uses 'amount')
    amt_col = amount_column if amount_column in df_feats.columns else ("amount" if "amount" in df_feats.columns else None)
    if amt_col:
        df_feats["amount_log"] = np.log1p(df_feats[amt_col].fillna(0))
    else:
        raise KeyError(f"Amount column not found in DataFrame (checked '{amount_column}' and 'amount').")

    # Time-based features: creditcard uses 'Time' (seconds), PaySim uses 'step' (hours).
    if time_column in df_feats.columns:
        # Time is in seconds from first transaction (coerce to numeric to avoid NaNs/strings)
        seconds = pd.to_numeric(df_feats[time_column], errors="coerce").fillna(0)
        df_feats["time_hours"] = seconds / 3600.0
        seconds_per_day = 24 * 3600
        df_feats["time_seconds_mod_day"] = seconds % seconds_per_day
        df_feats["hour_of_day"] = (df_feats["time_seconds_mod_day"] / 3600.0).fillna(0).astype(int)
    elif "step" in df_feats.columns:
        # PaySim step is in hours; derive hour-of-day proxy
        steps = pd.to_numeric(df_feats["step"], errors="coerce").fillna(0)
        df_feats["time_hours"] = steps
        df_feats["time_seconds_mod_day"] = (steps * 3600) % (24 * 3600)
        df_feats["hour_of_day"] = (df_feats["time_seconds_mod_day"] / 3600.0).fillna(0).astype(int)
    else:
        # Fallback: zeroed time features to avoid breaking pipelines
        df_feats["time_hours"] = 0
        df_feats["time_seconds_mod_day"] = 0
        df_feats["hour_of_day"] = 0

    return df_feats


def build_fraud_feature_table(
    df: pd.DataFrame,
    time_column: str = "Time",
    amount_column: str = "Amount",
    target_column: str = "Class",
    drop_original_time: bool = False,
    group_id_column: Optional[str] = None,
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

    # Simple rolling aggregates per entity (if an id column is provided)
    if group_id_column and group_id_column in df_feats.columns:
        df_feats = df_feats.sort_values([group_id_column, time_column] if time_column in df_feats.columns else [group_id_column])
        gb = df_feats.groupby(group_id_column)
        # Count of txns in past window proxies via expanding counts
        df_feats["tx_count_per_entity"] = gb.cumcount()
        # Amount running mean/std
        df_feats["amount_running_mean"] = gb[amount_column if amount_column in df_feats.columns else "Amount"].transform(
            lambda s: s.expanding().mean()
        )
        df_feats["amount_running_std"] = gb[amount_column if amount_column in df_feats.columns else "Amount"].transform(
            lambda s: s.expanding().std().fillna(0)
        )
        df_feats["amount_zscore_entity"] = (
            (df_feats[amount_column if amount_column in df_feats.columns else "Amount"] - df_feats["amount_running_mean"])
            / (df_feats["amount_running_std"] + 1e-6)
        )
        df_feats = df_feats.fillna(0)

    if drop_original_time and time_column in df_feats.columns:
        df_feats = df_feats.drop(columns=[time_column])

    # Ensure target column is present; fallback to common alternatives and fill missing values.
    # This protects against mixing datasets like CreditCard (Class) and PaySim (isFraud)
    # where concatenation introduces NaNs in one of the label columns.
    # Include lower-case variants for compatibility with PaySim loader normalization
    alternate_targets = [c for c in ("isFraud", "isfraud", "Class", "class") if c != target_column]
    if target_column not in df_feats.columns:
        for alt in alternate_targets:
            if alt in df_feats.columns:
                df_feats[target_column] = df_feats[alt]
                break
        else:
            raise KeyError(f"Target column '{target_column}' not found in DataFrame")
    else:
        for alt in alternate_targets:
            if alt in df_feats.columns:
                df_feats[target_column] = df_feats[target_column].fillna(df_feats[alt])

    # Coerce target to numeric, drop any remaining missing labels, and cast to int
    df_feats[target_column] = pd.to_numeric(df_feats[target_column], errors="coerce")
    if df_feats[target_column].isna().any():
        df_feats = df_feats.dropna(subset=[target_column]).reset_index(drop=True)
    df_feats[target_column] = df_feats[target_column].astype(int)

    return df_feats
