"""Prefect flow to train fusion meta-model from per-domain scores."""
from pathlib import Path

import mlflow
from prefect import flow, task

from uais.fusion.run_fusion import train_fusion
from uais.utils.mlflow_utils import load_mlflow_settings, setup_mlflow


@task
def train_fusion_task(cfg_path: Path):
    model, metrics = train_fusion(cfg_path)
    mlflow.log_metrics(metrics)
    return metrics


@flow(name="Fusion Flow")
def fusion_pipeline(cfg_path: str = "configs/fusion_baseline.yaml"):
    settings = load_mlflow_settings()
    setup_mlflow(experiment_name=settings["experiment_name"], tracking_uri=settings["tracking_uri"])

    with mlflow.start_run(run_name="fusion_flow"):
        metrics = train_fusion_task(Path(cfg_path))
        print("Fusion pipeline completed.", metrics)


if __name__ == "__main__":
    fusion_pipeline()
