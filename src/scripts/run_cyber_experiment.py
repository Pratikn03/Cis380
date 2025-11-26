"""CLI: end-to-end cyber intrusion run using in-repo components."""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from uais.anomaly.train_isolation_forest import compute_anomaly_score, train_isolation_forest
from uais.config.config_loader import load_config
from uais.data.load_cyber_data import load_cyber_data
from uais.features.cyber_features import build_cyber_feature_table
from uais.supervised.train_cyber_supervised import CyberModelConfig, train_cyber_model
from uais.utils.logging_utils import setup_logging
from uais.utils.metrics import compute_classification_metrics
from uais.utils.paths import domain_paths, ensure_directories

logger = setup_logging(__name__)


def save_json(obj: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
    logger.info("Saved %s", path)


def main():
    ensure_directories()
    cfg = load_config("cyber")
    target_col = cfg.get("data", {}).get("target", "label")
    drop_cols = cfg.get("data", {}).get("drop_columns")

    df_raw = load_cyber_data(cfg)
    df_feats = build_cyber_feature_table(df_raw, target_column=target_col, drop_columns=drop_cols)
    X = df_feats.drop(columns=[target_col])
    y = df_feats[target_col].astype(int)

    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.4, stratify=y, random_state=42)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, stratify=y_temp, random_state=42)

    train_cfg = cfg.get("training", {})
    model_cfg = CyberModelConfig(
        model_type=train_cfg.get("model_type", "hist_gb"),
        max_depth=train_cfg.get("max_depth", 6),
        learning_rate=train_cfg.get("learning_rate", 0.1),
        max_iter=train_cfg.get("max_iter", 200),
        n_estimators=train_cfg.get("n_estimators", 300),
        random_state=cfg.get("seed", 42),
    )

    model, val_metrics = train_cyber_model(X_train, y_train, X_val, y_val, model_cfg, use_pipeline=False)
    logger.info("Validation metrics: %s", val_metrics)

    if hasattr(model, "predict_proba"):
        test_proba = model.predict_proba(X_test)[:, 1]
    else:
        scores = model.decision_function(X_test)
        test_proba = 1.0 / (1.0 + np.exp(-scores))
    test_metrics = compute_classification_metrics(y_test.values, test_proba, threshold=0.5)
    logger.info("Test metrics: %s", test_metrics)

    contam = train_cfg.get("anomaly_contamination", 0.07)
    iso_model, scaler = train_isolation_forest(X_train, contamination=contam)
    iso_scores = compute_anomaly_score(iso_model, scaler, X_test)
    iso_metrics = compute_classification_metrics(y_test.values, iso_scores, threshold=0.5)
    logger.info("Isolation Forest metrics: %s", iso_metrics)

    paths = domain_paths("cyber")
    (paths["models"] / "supervised").mkdir(parents=True, exist_ok=True)
    joblib.dump(model, paths["models"] / "supervised" / "cyber_model.pkl")

    metrics_dir = paths["experiments"] / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    metrics = {
        "val": val_metrics,
        "test": test_metrics,
        "anomaly": iso_metrics,
    }
    save_json(metrics, metrics_dir / "metrics.json")
    pd.DataFrame(
        [
            {"Metric": "test_roc_auc", "Value": test_metrics.get("roc_auc", float("nan"))},
            {"Metric": "test_f1", "Value": test_metrics.get("f1", float("nan"))},
            {"Metric": "anomaly_roc_auc", "Value": iso_metrics.get("roc_auc", float("nan"))},
            {"Metric": "anomaly_f1", "Value": iso_metrics.get("f1", float("nan"))},
        ]
    ).to_csv(metrics_dir / "metrics.csv", index=False)

    scores_path = paths["experiments"] / "scores.csv"
    pd.DataFrame({"score": test_proba, "label": y_test.values}).to_csv(scores_path, index=False)
    logger.info("Saved scores to %s", scores_path)

    logger.info("Cyber experiment complete")


if __name__ == "__main__":
    main()
