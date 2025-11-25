"""Feature table builders delegating to existing UAIS modules."""
from pathlib import Path
from typing import Optional

import pandas as pd

try:
    from uais.features.behavior_features import build_behavior_feature_table
    from uais.features.fraud_features import build_fraud_features
    from uais.features.cyber_features import build_cyber_features
except Exception:  # pragma: no cover - fallback when uais not available
    build_behavior_feature_table = None
    build_fraud_features = None
    build_cyber_features = None

from ..paths import LAKE_DIR, PROCESSED_DIR


def build_behavior_features(raw_parquet: Optional[Path] = None, out_path: Optional[Path] = None) -> Path:
    if build_behavior_feature_table is None:
        raise ImportError("uais.features.behavior_features is not available.")
    raw_parquet = raw_parquet or (LAKE_DIR / "behavior" / "online_shoppers_intention.parquet")
    df = pd.read_parquet(raw_parquet)
    df_feats = build_behavior_feature_table(df)
    out_path = out_path or (PROCESSED_DIR / "behavior" / "behavior_features.parquet")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df_feats.to_parquet(out_path, index=False)
    return out_path


def build_fraud_features_table(raw_parquet: Optional[Path] = None, out_path: Optional[Path] = None) -> Path:
    if build_fraud_features is None:
        raise ImportError("uais.features.fraud_features is not available.")
    raw_parquet = raw_parquet or (LAKE_DIR / "fraud" / "creditcard.parquet")
    df = pd.read_parquet(raw_parquet)
    df_feats = build_fraud_features(df)
    out_path = out_path or (PROCESSED_DIR / "fraud" / "fraud_features.parquet")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df_feats.to_parquet(out_path, index=False)
    return out_path


def build_cyber_features_table(raw_parquet: Optional[Path] = None, out_path: Optional[Path] = None) -> Path:
    if build_cyber_features is None:
        raise ImportError("uais.features.cyber_features is not available.")
    raw_parquet = raw_parquet or (LAKE_DIR / "cyber" / "unsw_nb15.parquet")
    df = pd.read_parquet(raw_parquet)
    df_feats = build_cyber_features(df)
    out_path = out_path or (PROCESSED_DIR / "cyber" / "unsw_nb15_features.parquet")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df_feats.to_parquet(out_path, index=False)
    return out_path


__all__ = ["build_behavior_features", "build_fraud_features_table", "build_cyber_features_table"]
