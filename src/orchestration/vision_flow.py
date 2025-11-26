"""Stub Vision pipeline wrapper."""
from __future__ import annotations

from pathlib import Path

from uais.vision.train_vision_model import VisionConfig, run_vision_experiment
from uais.utils.logging_utils import setup_logging

logger = setup_logging(__name__)


def vision_pipeline(dataset_dir: str | None = None):
    """Run a small vision experiment (simple CNN by default)."""
    project_root = Path(__file__).resolve().parents[1]
    data_dir = Path(dataset_dir) if dataset_dir else project_root / "data" / "raw" / "vision" / "document_forgery"
    cfg = VisionConfig(dataset_dir=data_dir, epochs=1, batch_size=16, image_size=128)
    try:
        logger.info("Starting vision pipeline on %s", data_dir)
        metrics = run_vision_experiment(cfg)
        logger.info("Vision metrics: %s", metrics)
    except Exception as exc:  # pragma: no cover - best-effort
        logger.error("Vision pipeline failed: %s", exc)


__all__ = ["vision_pipeline"]
