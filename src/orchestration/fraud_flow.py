"""Best-effort fraud pipeline wrapper."""
from __future__ import annotations

from uais.utils.logging_utils import setup_logging

logger = setup_logging(__name__)


def fraud_pipeline():
    """Run the fraud experiment script."""
    try:
        from src.scripts.run_fraud_experiment import main as run_fraud
    except Exception as exc:  # pragma: no cover - import guard
        logger.error("Fraud pipeline import failed: %s", exc)
        return
    logger.info("Starting fraud pipeline via run_fraud_experiment")
    run_fraud()
    logger.info("Fraud pipeline complete")


__all__ = ["fraud_pipeline"]
