from __future__ import annotations

from celery import Celery

from app.core import settings

celery = Celery(
    "sentifargo",
    broker=settings.redis.url,
    backend=settings.redis.url,
)

celery.conf.update(
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)
