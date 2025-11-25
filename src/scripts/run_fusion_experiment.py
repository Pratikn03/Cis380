"""CLI: train a simple fusion meta-model using scores from each domain."""
import json
import numpy as np
from pathlib import Path

from uais.anomaly.train_autoencoder import train_autoencoder
from uais.config.config_loader import load_config
from uais.data.load_behavior_data import load_behavior_data
from uais.data.load_cyber_data import load_cyber_data
from uais.data.load_fraud_data import load_fraud_data
from uais.features.behavior_features import behavior_preprocessor, engineer_behavior_features
from uais.features.cyber_features import cyber_preprocessor, engineer_cyber_features
from uais.features.fraud_features import engineer_fraud_features, fraud_preprocessor
from uais.fusion.train_fusion_model import train_fusion_meta_model
from uais.supervised.train_cyber_supervised import train_cyber_supervised
from uais.supervised.train_fraud_supervised import train_fraud_supervised
from uais.utils.logging_utils import setup_logging
from uais.utils.paths import domain_paths, ensure_directories

logger = setup_logging(__name__)


def save_metrics(metrics: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    logger.info("Saved fusion metrics to %s", path)


def main():
    ensure_directories()
    cfg_fraud = load_config("fraud")
    cfg_cyber = load_config("cyber")
    cfg_behavior = load_config("behavior")

    # Train/score fraud model
    df_fraud = engineer_fraud_features(load_fraud_data(cfg_fraud))
    fraud_model, _ = train_fraud_supervised(df_fraud, cfg_fraud)
    fraud_scores = fraud_model.predict_proba(df_fraud.drop(columns=[cfg_fraud["data"]["target"]]))[:, 1]

    # Train/score cyber model
    df_cyber = engineer_cyber_features(load_cyber_data(cfg_cyber))
    cyber_model, _ = train_cyber_supervised(df_cyber, cfg_cyber)
    cyber_scores = cyber_model.predict_proba(df_cyber.drop(columns=[cfg_cyber["data"]["target"]]))[:, 1]

    # Train/score behavior autoencoder (use reconstruction error scaled to 0-1)
    df_behavior = engineer_behavior_features(load_behavior_data(cfg_behavior))
    behavior_pre = behavior_preprocessor(cfg_behavior)
    _, behavior_errors, _ = train_autoencoder(df_behavior, cfg_behavior["data"]["target"], behavior_pre, cfg_behavior, "behavior")
    behavior_scores = (behavior_errors - behavior_errors.min()) / (behavior_errors.ptp() + 1e-8)

    min_len = min(len(fraud_scores), len(cyber_scores), len(behavior_scores))
    score_dict = {
        "fraud": fraud_scores[:min_len],
        "cyber": cyber_scores[:min_len],
        "behavior": behavior_scores[:min_len],
    }
    labels = df_fraud[cfg_fraud["data"]["target"]].values[:min_len]

    fusion_model, fusion_metrics = train_fusion_meta_model(score_dict, labels, cfg_fraud)

    paths = domain_paths("fusion")
    metrics_path = paths["experiments"] / "metrics" / "fusion_metrics.json"
    save_metrics(fusion_metrics, metrics_path)
    logger.info("Fusion experiment complete")


if __name__ == "__main__":
    main()
