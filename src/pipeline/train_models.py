"""Train supervised models using processed feature tables with optional MLflow logging."""
from pathlib import Path
import json
from typing import Any, Dict

import numpy as np
import pandas as pd
import yaml
from sklearn.model_selection import train_test_split

from uais.supervised.train_fraud_supervised import FraudModelConfig, train_fraud_model
from uais.supervised.train_cyber_supervised import CyberModelConfig, train_cyber_model
from uais.utils.metrics import compute_classification_metrics, compute_confusion_matrix
from uais.utils.plotting import plot_roc_curve, plot_pr_curve


def _load_config(cfg_path: Path) -> Dict[str, Any]:
    with cfg_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _maybe_start_mlflow(cfg: Dict[str, Any]):
    mlflow_cfg = cfg.get("mlflow", {})
    enabled = mlflow_cfg.get("enabled", False)
    if not enabled:
        return None
    try:
        import mlflow
    except ImportError:  # pragma: no cover
        print("MLflow not installed; skipping tracking.")
        return None
    run_name = mlflow_cfg.get("run_name", "uais_run")
    tracking_uri = mlflow_cfg.get("tracking_uri")
    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(mlflow_cfg.get("experiment", "uais"))
    return mlflow.start_run(run_name=run_name)


def _log_mlflow_params_metrics(cfg: Dict[str, Any], model_params: Dict[str, Any], val_metrics: Dict[str, float], test_metrics: Dict[str, float]):
    try:
        import mlflow
    except ImportError:  # pragma: no cover
        return
    mlflow.log_params(model_params)
    for k, v in val_metrics.items():
        mlflow.log_metric(f"val_{k}", v)
    for k, v in test_metrics.items():
        mlflow.log_metric(f"test_{k}", v)


def train_from_config(cfg_path: Path):
    cfg = _load_config(cfg_path)
    domain = cfg.get("raw", {}).get("domain", "fraud").lower()
    feats_path = Path(cfg.get("features", {}).get("output", ""))
    if not feats_path.exists():
        raise FileNotFoundError(f"Feature file not found: {feats_path}")

    df = pd.read_parquet(feats_path)

    if domain == "fraud":
        target_col = "Class"
        ModelCfg = FraudModelConfig
        train_fn = train_fraud_model
    elif domain == "cyber":
        target_col = cfg.get("target_column", "label")
        ModelCfg = CyberModelConfig
        train_fn = train_cyber_model
    elif domain == "behavior":
        target_col = cfg.get("target_column", "Revenue")
        ModelCfg = FraudModelConfig  # reuse fraud config for tabular behavior
        train_fn = train_fraud_model
    else:
        raise ValueError("domain must be fraud | cyber | behavior")

    X = df.drop(columns=[target_col])
    y = df[target_col].astype(int)

    test_size = cfg.get("split", {}).get("test_size", 0.2)
    val_size = cfg.get("split", {}).get("val_size", 0.1)
    random_state = cfg.get("split", {}).get("random_state", 42)

    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=random_state
    )
    val_fraction = val_size / (1 - test_size)
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=1 - val_fraction, stratify=y_temp, random_state=random_state
    )

    model_cfg = ModelCfg(**cfg.get("model", {}))

    mlflow_run = _maybe_start_mlflow(cfg)
    try:
        model, val_metrics = train_fn(X_train, y_train, X_val, y_val, model_cfg)

        if hasattr(model, "predict_proba"):
            y_test_prob = model.predict_proba(X_test)[:, 1]
        else:
            scores = model.decision_function(X_test)
            y_test_prob = 1.0 / (1.0 + np.exp(-scores))

        test_metrics = compute_classification_metrics(y_test.values, y_test_prob, threshold=0.5)
        y_test_pred = (y_test_prob >= 0.5).astype(int)
        cm = compute_confusion_matrix(y_test.values, y_test_pred)

        metrics_all = {
            "val": val_metrics,
            "test": test_metrics,
            "cm": cm.tolist(),
        }

        _log_mlflow_params_metrics(
            cfg,
            model_params=model_cfg.__dict__,
            val_metrics=val_metrics,
            test_metrics=test_metrics,
        )
    finally:
        if mlflow_run is not None:
            try:
                import mlflow

                mlflow.end_run()
            except ImportError:
                pass

    metrics_dir = Path(cfg.get("metrics", {}).get("output_dir", f"experiments/{domain}/metrics"))
    metrics_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = metrics_dir / f"{domain}_metrics.json"
    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(metrics_all, f, indent=2)
    print(f"Saved metrics to {metrics_path}")

    plots_dir = Path(cfg.get("plots", {}).get("output_dir", f"experiments/{domain}/plots"))
    plots_dir.mkdir(parents=True, exist_ok=True)
    plot_roc_curve(y_test.values, y_test_prob, title=f"{domain} ROC", output_dir=plots_dir)
    plot_pr_curve(y_test.values, y_test_prob, title=f"{domain} PR", output_dir=plots_dir)
    print(f"Saved plots to {plots_dir}")

    return metrics_all


def main(cfg: str):
    train_from_config(Path(cfg))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train supervised model from config")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    args = parser.parse_args()
    main(args.config)
