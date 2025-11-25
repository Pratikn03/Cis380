"""Thin wrappers around existing pipeline ingestion utilities."""
from pathlib import Path
from typing import Optional

from ..paths import LAKE_DIR, RAW_DIR

try:
    from pipeline import ingest as pipeline_ingest
except Exception:  # pragma: no cover - pipeline is optional
    pipeline_ingest = None


def ingest_domain(domain: str, raw_dir: Optional[Path] = None, lake_dir: Optional[Path] = None) -> Path:
    if pipeline_ingest is None:
        raise ImportError("pipeline.ingest is not available in this environment.")

    raw_dir = raw_dir or RAW_DIR
    lake_dir = lake_dir or LAKE_DIR
    domain = domain.lower()
    if domain == "fraud":
        return pipeline_ingest.ingest_fraud(raw_dir, lake_dir)
    if domain == "cyber":
        return pipeline_ingest.ingest_cyber(raw_dir, lake_dir)
    if domain in {"behavior", "behaviour"}:
        return pipeline_ingest.ingest_behavior(raw_dir, lake_dir)
    raise ValueError("domain must be fraud | cyber | behavior")


__all__ = ["ingest_domain"]
