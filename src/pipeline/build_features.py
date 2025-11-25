"""Build feature tables from lake parquet into processed feature store."""
from pathlib import Path
import json
from typing import Any, Dict

import pandas as pd
import yaml

from uais.features.fraud_features import build_fraud_feature_table
from uais.features.cyber_features import build_cyber_feature_table
from uais.features.behavior_features import build_behavior_feature_table


def _load_config(cfg_path: Path) -> Dict[str, Any]:
    with cfg_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_features(cfg_path: Path) -> Path:
    cfg = _load_config(cfg_path)
    domain = cfg.get("raw", {}).get("domain", "fraud").lower()

    lake_path = Path(cfg.get("lake", {}).get("path", ""))
    if not lake_path:
        raise ValueError("lake.path is required in config")
    if lake_path.is_dir():
        parquet_files = sorted(lake_path.glob("*.parquet"))
        if not parquet_files:
            raise FileNotFoundError(f"No parquet found in {lake_path}")
        lake_path = parquet_files[-1]

    print(f"Loading lake parquet: {lake_path}")
    df = pd.read_parquet(lake_path)

    if domain == "fraud":
        df_feats = build_fraud_feature_table(df, time_column="Time", amount_column="Amount", target_column="Class")
    elif domain == "cyber":
        target_col = cfg.get("target_column", "label")
        drop_cols = [c for c in ["id", "attack_cat"] if c in df.columns]
        df_feats = build_cyber_feature_table(df_raw=df, target_column=target_col, drop_columns=drop_cols)
    elif domain == "behavior":
        target_col = cfg.get("target_column", "Revenue")
        df_feats = build_behavior_feature_table(df_raw=df, target_column=target_col, drop_columns=None)
    else:
        raise ValueError("domain must be fraud | cyber | behavior")

    out_path = Path(cfg.get("features", {}).get("output", f"data/processed/{domain}/features.parquet"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df_feats.to_parquet(out_path, index=False)
    print(f"Saved features to {out_path} with shape {df_feats.shape}")

    meta = {
        "domain": domain,
        "input": str(lake_path),
        "output": str(out_path),
        "rows": int(df_feats.shape[0]),
        "cols": int(df_feats.shape[1]),
    }
    meta_path = out_path.with_suffix(".json")
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"Wrote feature metadata to {meta_path}")

    return out_path


def main(cfg: str):
    build_features(Path(cfg))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build features from lake parquet")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    args = parser.parse_args()
    main(args.config)
