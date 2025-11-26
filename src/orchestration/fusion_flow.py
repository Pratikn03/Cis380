"""Best-effort fusion pipeline wrapper."""
from __future__ import annotations

from uais.utils.logging_utils import setup_logging

logger = setup_logging(__name__)


def fusion_pipeline():
    """Run the fusion experiment script."""
    try:
        from src.scripts.run_fusion_experiment import main as run_fusion
    except Exception as exc:  # pragma: no cover - import guard
        logger.error("Fusion pipeline import failed: %s", exc)
        return
    logger.info("Starting fusion pipeline via run_fusion_experiment")
    run_fusion()
    logger.info("Fusion pipeline complete")


__all__ = ["fusion_pipeline"]
