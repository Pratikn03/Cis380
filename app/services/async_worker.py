from __future__ import annotations

import os

from celery import Celery

from app.services.risk_engine import analyze_risk


def _get_broker_url() -> str:
    return os.getenv("CELERY_BROKER_URL") or os.getenv("REDIS_URL", "redis://localhost:6379/0")


def _get_backend_url() -> str:
    return os.getenv("CELERY_BACKEND_URL") or os.getenv("REDIS_URL", "redis://localhost:6379/0")


celery = Celery(
    "sentinelforge",
    broker=_get_broker_url(),
    backend=_get_backend_url(),
)


@celery.task
def async_risk(payload: dict) -> dict:
    """Run risk scoring in the background."""
    return analyze_risk(payload)
