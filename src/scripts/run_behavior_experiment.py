"""CLI: behavior anomaly detection run (autoencoder + LOF)."""
import json
from pathlib import Path

from uais.anomaly.train_autoencoder import train_autoencoder
from uais.anomaly.train_lof import train_lof
from uais.anomaly.evaluate_anomaly import evaluate_anomaly_scores
from uais.config.config_loader import load_config
from uais.data.load_behavior_data import load_behavior_data
from uais.features.behavior_features import behavior_preprocessor, engineer_behavior_features
from uais.utils.logging_utils import setup_logging
from uais.utils.paths import domain_paths, ensure_directories

logger = setup_logging(__name__)


def save_metrics(metrics: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    logger.info("Saved metrics to %s", path)


def main():
    ensure_directories()
    domain = "behavior"
    cfg = load_config(domain)
    df = load_behavior_data(cfg)
    df = engineer_behavior_features(df)

    preprocessor = behavior_preprocessor(cfg)
    ae_model, ae_scores, y_true = train_autoencoder(df, cfg["data"]["target"], preprocessor, cfg, domain)
    ae_metrics = evaluate_anomaly_scores(y_true, ae_scores, cfg.get("training", {}).get("anomaly_contamination", 0.05))
    ae_metrics = {f"autoencoder_{k}": v for k, v in ae_metrics.items()}

    lof_model, lof_scores, _ = train_lof(df, cfg["data"]["target"], preprocessor, cfg, domain)
    lof_metrics = evaluate_anomaly_scores(y_true, lof_scores, cfg.get("training", {}).get("anomaly_contamination", 0.05))
    lof_metrics = {f"lof_{k}": v for k, v in lof_metrics.items()}

    combined_metrics = {**ae_metrics, **lof_metrics}

    paths = domain_paths(domain)
    metrics_path = paths["experiments"] / "metrics" / "behavior_metrics.json"
    save_metrics(combined_metrics, metrics_path)

    logger.info("Behavior experiment complete")


if __name__ == "__main__":
    main()
