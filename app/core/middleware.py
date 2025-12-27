"""
SentinelForge Production Middleware & Error Handling
Rate limiting, security headers, logging, and error handling
"""

from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Callable

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("sentinelforge.middleware")


# ============================================
# Custom Exceptions
# ============================================


class SentinelForgeException(Exception):
    """Base exception for SentinelForge."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: dict | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(SentinelForgeException):
    """Validation error."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class AuthenticationError(SentinelForgeException):
    """Authentication error."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR",
        )


class AuthorizationError(SentinelForgeException):
    """Authorization error."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR",
        )


class RateLimitError(SentinelForgeException):
    """Rate limit exceeded error."""

    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="Rate limit exceeded",
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after},
        )


class ModelError(SentinelForgeException):
    """ML model error."""

    def __init__(self, message: str, model_name: str | None = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="MODEL_ERROR",
            details={"model": model_name} if model_name else {},
        )


class NotFoundError(SentinelForgeException):
    """Resource not found error."""

    def __init__(self, resource: str, resource_id: str | None = None):
        super().__init__(
            message=f"{resource} not found",
            status_code=404,
            error_code="NOT_FOUND",
            details={"resource": resource, "id": resource_id} if resource_id else {},
        )


# ============================================
# Error Response Model
# ============================================


def create_error_response(
    request_id: str,
    status_code: int,
    error_code: str,
    message: str,
    details: dict | None = None,
    path: str | None = None,
) -> dict:
    """Create a standardized error response."""
    return {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
            "details": details or {},
            "path": path,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    }


# ============================================
# Exception Handlers
# ============================================


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers."""

    @app.exception_handler(SentinelForgeException)
    async def sentinelforge_exception_handler(
        request: Request, exc: SentinelForgeException
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        logger.warning(
            "SentinelForge exception: %s [%s] request_id=%s",
            exc.message,
            exc.error_code,
            request_id,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=create_error_response(
                request_id=request_id,
                status_code=exc.status_code,
                error_code=exc.error_code,
                message=exc.message,
                details=exc.details,
                path=str(request.url.path),
            ),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        error_code = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            422: "UNPROCESSABLE_ENTITY",
            429: "TOO_MANY_REQUESTS",
            500: "INTERNAL_SERVER_ERROR",
        }.get(exc.status_code, "HTTP_ERROR")

        return JSONResponse(
            status_code=exc.status_code,
            content=create_error_response(
                request_id=request_id,
                status_code=exc.status_code,
                error_code=error_code,
                message=str(exc.detail),
                path=str(request.url.path),
            ),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        logger.exception(
            "Unhandled exception request_id=%s: %s",
            request_id,
            str(exc),
        )
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                request_id=request_id,
                status_code=500,
                error_code="INTERNAL_SERVER_ERROR",
                message="An internal error occurred",
                path=str(request.url.path),
            ),
        )


# ============================================
# Rate Limiting Middleware
# ============================================


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""

    def __init__(
        self,
        app: FastAPI,
        requests_per_minute: int = 60,
        window_seconds: int = 60,
        enabled: bool = True,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds
        self.enabled = enabled
        self.request_counts: dict[str, list[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP from request."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if client is rate limited."""
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old entries
        self.request_counts[client_ip] = [
            ts for ts in self.request_counts[client_ip] if ts > window_start
        ]

        # Check rate limit
        if len(self.request_counts[client_ip]) >= self.requests_per_minute:
            return True

        # Add current request
        self.request_counts[client_ip].append(now)
        return False

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.enabled:
            return await call_next(request)

        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/metrics", "/ready"]:
            return await call_next(request)

        client_ip = self._get_client_ip(request)

        if self._is_rate_limited(client_ip):
            request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
            return JSONResponse(
                status_code=429,
                content=create_error_response(
                    request_id=request_id,
                    status_code=429,
                    error_code="RATE_LIMIT_EXCEEDED",
                    message="Too many requests",
                    details={"retry_after": self.window_seconds},
                    path=str(request.url.path),
                ),
                headers={"Retry-After": str(self.window_seconds)},
            )

        return await call_next(request)


# ============================================
# Request ID Middleware
# ============================================


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to each request."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


# ============================================
# Logging Middleware
# ============================================


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests with timing."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        request_id = getattr(request.state, "request_id", "unknown")

        # Log request
        logger.info(
            "Request started: %s %s request_id=%s client=%s",
            request.method,
            request.url.path,
            request_id,
            request.client.host if request.client else "unknown",
        )

        response = await call_next(request)

        # Log response
        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "Request completed: %s %s status=%d duration=%.2fms request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )

        # Add timing header
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        return response


# ============================================
# Security Headers Middleware
# ============================================


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"

        # CSP for API (strict)
        if request.url.path.startswith("/api/"):
            response.headers["Content-Security-Policy"] = "default-src 'none'"

        return response


# ============================================
# Setup Function
# ============================================


def setup_production_middleware(
    app: FastAPI,
    cors_origins: list[str] | None = None,
    rate_limit_enabled: bool = True,
    rate_limit_requests: int = 100,
    rate_limit_window: int = 60,
) -> None:
    """Setup all production middleware and error handlers."""

    # Register exception handlers
    register_exception_handlers(app)

    # Add middleware (order matters - last added is first executed)

    # 1. Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # 2. Request logging
    app.add_middleware(RequestLoggingMiddleware)

    # 3. Rate limiting
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=rate_limit_requests,
        window_seconds=rate_limit_window,
        enabled=rate_limit_enabled,
    )

    # 4. Request ID
    app.add_middleware(RequestIDMiddleware)

    # 5. CORS (always last - first executed)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Response-Time"],
    )

    logger.info("Production middleware configured successfully")
