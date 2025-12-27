"""
SentinelForge Core Module
Configuration, middleware, and health checks for production deployment
"""

from app.core.config import Settings, get_settings, settings
from app.core.middleware import (
    SentinelForgeException,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    ModelError,
    NotFoundError,
    setup_production_middleware,
)
from app.core.health import router as health_router

__all__ = [
    # Config
    "Settings",
    "get_settings",
    "settings",
    # Exceptions
    "SentinelForgeException",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "RateLimitError",
    "ModelError",
    "NotFoundError",
    # Middleware
    "setup_production_middleware",
    # Health
    "health_router",
]
