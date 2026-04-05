"""Compatibility entrypoint for the canonical FastAPI app.

Use `uvicorn app.main:app` in production. This module keeps the scaffold in sync
by delegating to the real backend when available.
"""

from __future__ import annotations

try:
    from app.main import app  # type: ignore
except Exception:  # pragma: no cover
    from fastapi import FastAPI

    from src.api.health import router as health_router
    from src.api.monitoring import router as monitoring_router

    app = FastAPI(title="SentinelForge")
    app.include_router(health_router)
    app.include_router(monitoring_router)
