"""
Sentifargo Core Module
Configuration, middleware, and health checks for production deployment
"""

from app.core.config import Settings, get_settings, settings
from app.core.middleware import (
    SentifargoException,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    ModelError,
    NotFoundError,
    setup_production_middleware,
)
from app.core.auth import check_token_query, require_auth
from app.core.health import router as health_router

__all__ = [
    # Config
    "Settings",
    "get_settings",
    "settings",
    # Exceptions
    "SentifargoException",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "RateLimitError",
    "ModelError",
    "NotFoundError",
    # Middleware
    "setup_production_middleware",
    # Auth
    "require_auth",
    "check_token_query",
    # Health
    "health_router",
]
