"""Utilities for MLflow experiment tracking."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import mlflow
import yaml

from uais.utils.paths import PROJECT_ROOT


def load_mlflow_settings(config_path: str | Path | None = None) -> Dict[str, str]:
    """Load tracking URI and experiment name from YAML."""
    path = Path(config_path) if config_path else PROJECT_ROOT / "mlflow_config.yaml"
    if not path.exists():
        return {"tracking_uri": "http://localhost:5000", "experiment_name": "UAISV_Experiments"}
    cfg = yaml.safe_load(path.read_text())
    ml_cfg = cfg.get("mlflow", {}) if isinstance(cfg, dict) else {}
    return {
        "tracking_uri": ml_cfg.get("tracking_uri", "http://localhost:5000"),
        "experiment_name": ml_cfg.get("experiment_name", "UAISV_Experiments"),
    }


def setup_mlflow(experiment_name: str = "UAISV_Experiments", tracking_uri: str | None = None) -> None:
    """Configure the MLflow tracking URI and experiment name."""
    mlflow.set_tracking_uri(tracking_uri or "http://localhost:5000")
    mlflow.set_experiment(experiment_name)
    print(f"MLflow experiment set: {experiment_name}")


def log_run(params: Dict[str, float] | None, metrics: Dict[str, float]) -> None:
    """Log parameters and metrics to MLflow inside a single run."""
    params = params or {}
    with mlflow.start_run():
        for key, value in params.items():
            mlflow.log_param(key, value)
        for key, value in metrics.items():
            mlflow.log_metric(key, value)
    print("Metrics logged to MLflow.")


__all__ = ["setup_mlflow", "log_run", "load_mlflow_settings"]
