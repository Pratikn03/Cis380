"""CLI: behavior anomaly detection run (autoencoder + LOF) using current components."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from uais.anomaly.evaluate_anomaly import evaluate_anomaly_scores
from uais.anomaly.train_autoencoder import train_autoencoder
from uais.anomaly.train_lof import train_lof
from uais.config.config_loader import load_config
from uais.data.load_behavior_data import load_behavior_data
from uais.features.behavior_features import build_behavior_feature_table
from uais.utils.logging_utils import setup_logging
from uais.utils.paths import domain_paths, ensure_directories

logger = setup_logging(__name__)


def save_json(obj: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
    logger.info("Saved %s", path)


def main():
    ensure_directories()
    cfg = load_config("behavior")
    target_col = cfg.get("data", {}).get("target", "Revenue")
    drop_cols = cfg.get("data", {}).get("drop_columns")

    df_raw = load_behavior_data(cfg)
    df_feats = build_behavior_feature_table(df_raw, target_column=target_col, drop_columns=drop_cols)
    X = df_feats.drop(columns=[target_col])
    y = df_feats[target_col].astype(int)

    # Split for evaluation even though models are unsupervised.
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, stratify=y, random_state=42)

    preprocessor = StandardScaler()

    ae_model, _, _ = train_autoencoder(
        pd.concat([X_train, y_train], axis=1), target_col, preprocessor, cfg, "behavior"
    )
    ae_scores_test = ae_model.predict(preprocessor.transform(X_test))
    ae_recon_error = np.mean((preprocessor.transform(X_test) - ae_scores_test) ** 2, axis=1)
    ae_metrics = evaluate_anomaly_scores(
        y_test, ae_recon_error, cfg.get("training", {}).get("anomaly_contamination", 0.05)
    )
    ae_metrics = {f"autoencoder_{k}": v for k, v in ae_metrics.items()}

    lof_model, _, _ = train_lof(
        pd.concat([X_train, y_train], axis=1), target_col, preprocessor, cfg, "behavior"
    )
    lof_scores_test = -lof_model.score_samples(preprocessor.transform(X_test))
    lof_metrics = evaluate_anomaly_scores(
        y_test, lof_scores_test, cfg.get("training", {}).get("anomaly_contamination", 0.05)
    )
    lof_metrics = {f"lof_{k}": v for k, v in lof_metrics.items()}

    metrics = {**ae_metrics, **lof_metrics}

    paths = domain_paths("behavior")
    metrics_dir = paths["experiments"] / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    save_json(metrics, metrics_dir / "metrics.json")
    pd.DataFrame(
        [{"Metric": k, "Value": v} for k, v in metrics.items()]
    ).to_csv(metrics_dir / "metrics.csv", index=False)

    # Normalize autoencoder errors for fusion friendliness.
    ae_norm = (ae_recon_error - ae_recon_error.min()) / (np.ptp(ae_recon_error) + 1e-8)
    scores_path = paths["experiments"] / "scores.csv"
    pd.DataFrame({"score": ae_norm, "label": y_test.values}).to_csv(scores_path, index=False)
    logger.info("Saved scores to %s", scores_path)

    logger.info("Behavior experiment complete")


if __name__ == "__main__":
    main()
