"""
Feature engineering for CERT r4.2 (Insider Threat) behavior data.

This module provides functions to extract and engineer features from CERT logon and activity logs for anomaly detection.
"""

import pandas as pd
import numpy as np

def add_cert_behavior_features(df: pd.DataFrame, time_col: str = "date", user_col: str = "user") -> pd.DataFrame:
    """
    Add engineered features to CERT behavior data.
    Features include hour, dayofweek, and session statistics.

    Args:
        df (pd.DataFrame): Raw CERT logon/activity data.
        time_col (str): Name of the datetime column.
        user_col (str): Name of the user column.
    Returns:
        pd.DataFrame: DataFrame with new features.
    """
    df = df.copy()
    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=[time_col])
    df = df.sort_values([user_col, time_col])
    df["hour"] = df[time_col].dt.hour
    df["dayofweek"] = df[time_col].dt.dayofweek
    # Example: session length (if session_id exists)
    if "session_id" in df.columns:
        session_lengths = df.groupby("session_id").size().rename("session_length")
        df = df.join(session_lengths, on="session_id")
    return df
