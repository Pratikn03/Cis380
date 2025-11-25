"""Utilities for MLflow experiment tracking."""

from __future__ import annotations

from typing import Dict

import mlflow


def setup_mlflow(experiment_name: str = "UAISV_Experiments", tracking_uri: str | None = None) -> None:
    """Configure the MLflow tracking URI and experiment name."""

    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)
    else:
        # default to local server
        mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment(experiment_name)
    print(f"MLflow experiment set: {experiment_name}")


def log_metrics(params: Dict[str, float], metrics: Dict[str, float]) -> None:
    """Log parameters and metrics to MLflow inside a single run."""

    with mlflow.start_run():
        for key, value in params.items():
            mlflow.log_param(key, value)
        for key, value in metrics.items():
            mlflow.log_metric(key, value)
    print("Metrics logged to MLflow.")


__all__ = ["setup_mlflow", "log_metrics"]
