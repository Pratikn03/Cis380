"""CLI: end-to-end cyber intrusion run."""
import json
from pathlib import Path

from uais.anomaly.train_isolation_forest import train_isolation_forest
from uais.anomaly.evaluate_anomaly import evaluate_anomaly_scores
from uais.config.config_loader import load_config
from uais.data.load_cyber_data import load_cyber_data
from uais.features.cyber_features import cyber_preprocessor, engineer_cyber_features
from uais.supervised.train_cyber_supervised import train_cyber_supervised
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
    domain = "cyber"
    cfg = load_config(domain)
    df = load_cyber_data(cfg)
    df = engineer_cyber_features(df)

    sup_model, sup_metrics = train_cyber_supervised(df, cfg)

    preprocessor = cyber_preprocessor(cfg)
    iso_model, scores, y_true = train_isolation_forest(df, cfg["data"]["target"], preprocessor, cfg, domain)
    iso_metrics = evaluate_anomaly_scores(y_true, scores, cfg.get("training", {}).get("anomaly_contamination", 0.05))
    iso_metrics = {f"anomaly_{k}": v for k, v in iso_metrics.items()}

    combined_metrics = {**sup_metrics, **iso_metrics}

    paths = domain_paths(domain)
    metrics_path = paths["experiments"] / "metrics" / "cyber_metrics.json"
    save_metrics(combined_metrics, metrics_path)

    logger.info("Cyber experiment complete")


if __name__ == "__main__":
    main()
