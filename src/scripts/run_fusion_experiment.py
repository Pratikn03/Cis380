"""CLI: train a fusion meta-model from fraud, cyber, and behavior scores."""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from uais.config.config_loader import load_config
from uais.data.load_behavior_data import load_behavior_data
from uais.data.load_cyber_data import load_cyber_data
from uais.data.load_fraud_data import load_fraud_data
from uais.features.behavior_features import build_behavior_feature_table
from uais.features.cyber_features import build_cyber_feature_table
from uais.features.fraud_features import build_fraud_feature_table
from uais.fusion.build_embeddings import generate_meta_features
from uais.fusion.train_fusion_model import train_fusion_meta_model
from uais.supervised.train_cyber_supervised import CyberModelConfig, train_cyber_model
from uais.supervised.train_fraud_supervised import FraudModelConfig, train_fraud_model
from uais.anomaly.train_autoencoder import train_autoencoder
from uais.utils.logging_utils import setup_logging
from uais.utils.paths import domain_paths, ensure_directories

logger = setup_logging(__name__)


def save_json(obj: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
    logger.info("Saved %s", path)


def _train_fraud_scores(cfg: dict) -> tuple[np.ndarray, np.ndarray]:
    df = build_fraud_feature_table(load_fraud_data(cfg), time_column="Time", amount_column="Amount", target_column="Class")
    X = df.drop(columns=["Class"])
    y = df["Class"].astype(int)
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    model_cfg = FraudModelConfig(
        model_type=cfg.get("training", {}).get("model_type", "hist_gb"),
        max_depth=cfg.get("training", {}).get("max_depth", 4),
        learning_rate=cfg.get("training", {}).get("learning_rate", 0.1),
        max_iter=cfg.get("training", {}).get("max_iter", 200),
        n_estimators=cfg.get("training", {}).get("n_estimators", 200),
        random_state=cfg.get("seed", 42),
    )
    model, _ = train_fraud_model(X_train, y_train, X_val, y_val, model_cfg)
    scores = model.predict_proba(X)[:, 1]
    return scores, y.values


def _train_cyber_scores(cfg: dict) -> tuple[np.ndarray, np.ndarray]:
    df_raw = load_cyber_data(cfg)
    df = build_cyber_feature_table(df_raw, target_column=cfg.get("data", {}).get("target", "label"),
                                   drop_columns=cfg.get("data", {}).get("drop_columns"))
    X = df.drop(columns=[cfg.get("data", {}).get("target", "label")])
    y = df[cfg.get("data", {}).get("target", "label")].astype(int)
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    model_cfg = CyberModelConfig(
        model_type=cfg.get("training", {}).get("model_type", "hist_gb"),
        max_depth=cfg.get("training", {}).get("max_depth", 6),
        learning_rate=cfg.get("training", {}).get("learning_rate", 0.1),
        max_iter=cfg.get("training", {}).get("max_iter", 200),
        n_estimators=cfg.get("training", {}).get("n_estimators", 300),
        random_state=cfg.get("seed", 42),
    )
    model, _ = train_cyber_model(X_train, y_train, X_val, y_val, model_cfg, use_pipeline=False)
    scores = model.predict_proba(X)[:, 1] if hasattr(model, "predict_proba") else model.decision_function(X)
    return scores, y.values


def _train_behavior_scores(cfg: dict) -> tuple[np.ndarray, np.ndarray]:
    df_raw = load_behavior_data(cfg)
    target_col = cfg.get("data", {}).get("target", "Revenue")
    df = build_behavior_feature_table(df_raw, target_column=target_col, drop_columns=cfg.get("data", {}).get("drop_columns"))
    X = df.drop(columns=[target_col])
    y = df[target_col].astype(int)
    preprocessor = StandardScaler()
    ae_model, _, _ = train_autoencoder(df, target_col, preprocessor, cfg, "behavior")
    recon = ae_model.predict(preprocessor.transform(X))
    errors = np.mean((preprocessor.transform(X) - recon) ** 2, axis=1)
    scores = (errors - errors.min()) / (np.ptp(errors) + 1e-8)
    return scores, y.values


def main():
    ensure_directories()
    cfg_fraud = load_config("fraud")
    cfg_cyber = load_config("cyber")
    cfg_behavior = load_config("behavior")

    fraud_scores, fraud_labels = _train_fraud_scores(cfg_fraud)
    cyber_scores, _ = _train_cyber_scores(cfg_cyber)
    behavior_scores, _ = _train_behavior_scores(cfg_behavior)

    min_len = min(len(fraud_scores), len(cyber_scores), len(behavior_scores))
    score_dict = {
        "fraud": fraud_scores[:min_len],
        "cyber": cyber_scores[:min_len],
        "behavior": behavior_scores[:min_len],
    }
    labels = fraud_labels[:min_len]

    fusion_model, fusion_metrics = train_fusion_meta_model(score_dict, labels, cfg_fraud)

    paths = domain_paths("fusion")
    metrics_dir = paths["experiments"] / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    save_json(fusion_metrics, metrics_dir / "metrics.json")
    pd.DataFrame(
        [
            {"Metric": "roc_auc", "Value": fusion_metrics.get("roc_auc", float("nan"))},
            {"Metric": "f1", "Value": fusion_metrics.get("f1", float("nan"))},
            {"Metric": "cv_roc_auc_mean", "Value": fusion_metrics.get("cv_roc_auc_mean", float("nan"))},
        ]
    ).to_csv(metrics_dir / "metrics.csv", index=False)

    # Compute and save fusion scores for dashboard/API
    artifact = paths["models"] / "fusion_meta_model.pkl"
    if artifact.exists():
        bundle = joblib.load(artifact)
        scaler = bundle["scaler"]
        meta_model = bundle["model"]
        X_meta = generate_meta_features(score_dict)
        proba = meta_model.predict_proba(scaler.transform(X_meta))[:, 1]
        pd.DataFrame({"fusion_score": proba, "label": labels}).to_csv(
            paths["experiments"] / "fusion_scores.csv", index=False
        )
        logger.info("Saved fusion scores to %s", paths["experiments"] / "fusion_scores.csv")

    logger.info("Fusion experiment complete")


if __name__ == "__main__":
    main()
