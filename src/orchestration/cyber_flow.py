"""Best-effort cyber pipeline wrapper."""
from __future__ import annotations

from uais.utils.logging_utils import setup_logging

logger = setup_logging(__name__)


def cyber_pipeline():
    """Run the cyber experiment script."""
    try:
        from src.scripts.run_cyber_experiment import main as run_cyber
    except Exception as exc:  # pragma: no cover - import guard
        logger.error("Cyber pipeline import failed: %s", exc)
        return
    logger.info("Starting cyber pipeline via run_cyber_experiment")
    run_cyber()
    logger.info("Cyber pipeline complete")


__all__ = ["cyber_pipeline"]
