"""Stub NLP pipeline wrapper."""
from __future__ import annotations

from pathlib import Path

from uais.nlp.train_text_classifier import NLPConfig, run_text_experiment
from uais.utils.logging_utils import setup_logging

logger = setup_logging(__name__)


def nlp_pipeline(dataset_path: str | None = None):
    """Run the baseline TF-IDF + logistic regression NLP experiment."""
    project_root = Path(__file__).resolve().parents[1]
    csv_path = Path(dataset_path) if dataset_path else project_root / "data" / "raw" / "nlp" / "enron_emails.csv"
    cfg = NLPConfig(
        dataset_path=csv_path,
        text_column="content",
        label_column="label",
        max_samples=5000,
        max_features=5000,
    )
    try:
        logger.info("Starting NLP pipeline on %s", cfg.dataset_path)
        metrics = run_text_experiment(cfg)
        logger.info("NLP metrics: %s", metrics)
    except Exception as exc:  # pragma: no cover - best-effort
        logger.error("NLP pipeline failed: %s", exc)


__all__ = ["nlp_pipeline"]
