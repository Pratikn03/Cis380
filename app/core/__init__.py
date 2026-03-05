"""
Sentifargo Core Module
Configuration, middleware, and health checks for production deployment.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "Settings",
    "get_settings",
    "settings",
    "SentifargoException",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "RateLimitError",
    "ModelError",
    "NotFoundError",
    "setup_production_middleware",
    "health_router",
]


def __getattr__(name: str) -> Any:
    if name in {"Settings", "get_settings", "settings"}:
        from app.core.config import Settings, get_settings, settings

        return {"Settings": Settings, "get_settings": get_settings, "settings": settings}[name]
    if name in {
        "SentifargoException",
        "ValidationError",
        "AuthenticationError",
        "AuthorizationError",
        "RateLimitError",
        "ModelError",
        "NotFoundError",
        "setup_production_middleware",
    }:
        from app.core import middleware as _middleware

        return getattr(_middleware, name)
    if name == "health_router":
        from app.core.health import router as health_router

        return health_router
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
