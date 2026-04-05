from __future__ import annotations

import os

from celery import Celery

from app.services.risk_engine import analyze_risk


def _get_conf(key: str, default: str = "redis://localhost:6379/0") -> str:
    return os.getenv(key) or os.getenv("REDIS_URL", default)


celery = Celery(
    "Sentifargo",
    broker=_get_conf("CELERY_BROKER_URL"),
    backend=_get_conf("CELERY_BACKEND_URL"),
)


@celery.task
def async_risk(payload: dict) -> dict:
    """Run risk scoring in the background."""
    return analyze_risk(payload)
