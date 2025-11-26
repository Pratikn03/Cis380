"""Best-effort behavior pipeline wrapper."""
from __future__ import annotations

from uais.utils.logging_utils import setup_logging

logger = setup_logging(__name__)


def behavior_pipeline():
    """Run the behavior experiment script."""
    try:
        from src.scripts.run_behavior_experiment import main as run_behavior
    except Exception as exc:  # pragma: no cover - import guard
        logger.error("Behavior pipeline import failed: %s", exc)
        return
    logger.info("Starting behavior pipeline via run_behavior_experiment")
    run_behavior()
    logger.info("Behavior pipeline complete")


__all__ = ["behavior_pipeline"]
