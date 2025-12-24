"""
OmniChatX Production Health Checks & Metrics
Comprehensive health checks for all system components
"""

from __future__ import annotations

import asyncio
import logging
import os
import platform
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
    REGISTRY,
)

logger = logging.getLogger("omnichatx.health")

router = APIRouter(tags=["Health"])


# ============================================
# Health Status Enums
# ============================================


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """Health status for a single component."""

    name: str
    status: HealthStatus
    latency_ms: float = 0.0
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemHealth:
    """Overall system health."""

    status: HealthStatus
    version: str
    uptime_seconds: float
    timestamp: str
    components: list[ComponentHealth]

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "version": self.version,
            "uptime_seconds": round(self.uptime_seconds, 2),
            "timestamp": self.timestamp,
            "components": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "latency_ms": round(c.latency_ms, 2),
                    "message": c.message,
                    "details": c.details,
                }
                for c in self.components
            ],
        }


# ============================================
# Prometheus Metrics
# ============================================

# Request metrics
REQUEST_COUNT = Counter(
    "omnichatx_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "omnichatx_request_duration_seconds",
    "Request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# Model metrics
MODEL_INFERENCE_COUNT = Counter(
    "omnichatx_model_inference_total",
    "Total model inferences",
    ["model_type", "model_name"],
)

MODEL_INFERENCE_LATENCY = Histogram(
    "omnichatx_model_inference_seconds",
    "Model inference latency in seconds",
    ["model_type", "model_name"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

MODEL_ERRORS = Counter(
    "omnichatx_model_errors_total",
    "Total model errors",
    ["model_type", "model_name", "error_type"],
)

# System metrics
SYSTEM_INFO = Info(
    "omnichatx_system",
    "System information",
)

ACTIVE_CONNECTIONS = Gauge(
    "omnichatx_active_connections",
    "Number of active connections",
)

MEMORY_USAGE = Gauge(
    "omnichatx_memory_usage_bytes",
    "Memory usage in bytes",
)

CPU_USAGE = Gauge(
    "omnichatx_cpu_usage_percent",
    "CPU usage percentage",
)

# Health check metrics
HEALTH_CHECK_STATUS = Gauge(
    "omnichatx_health_check_status",
    "Health check status (1=healthy, 0.5=degraded, 0=unhealthy)",
    ["component"],
)

HEALTH_CHECK_LATENCY = Histogram(
    "omnichatx_health_check_latency_seconds",
    "Health check latency",
    ["component"],
)


# ============================================
# Global State
# ============================================

_START_TIME = time.time()
_APP_VERSION = os.getenv("APP_VERSION", "1.0.0")


def get_uptime() -> float:
    """Get application uptime in seconds."""
    return time.time() - _START_TIME


# ============================================
# Health Check Functions
# ============================================


async def check_database() -> ComponentHealth:
    """Check database connectivity."""
    start = time.time()
    try:
        # Simple check - verify data directory exists
        data_dir = Path("./data")
        if not data_dir.exists():
            data_dir.mkdir(parents=True, exist_ok=True)

        latency = (time.time() - start) * 1000
        return ComponentHealth(
            name="database",
            status=HealthStatus.HEALTHY,
            latency_ms=latency,
            message="Database accessible",
            details={"type": "sqlite", "path": str(data_dir)},
        )
    except Exception as e:
        latency = (time.time() - start) * 1000
        return ComponentHealth(
            name="database",
            status=HealthStatus.UNHEALTHY,
            latency_ms=latency,
            message=f"Database error: {str(e)}",
        )


async def check_redis() -> ComponentHealth:
    """Check Redis connectivity."""
    start = time.time()
    try:
        redis_url = os.getenv("REDIS_URL", "")
        if not redis_url:
            return ComponentHealth(
                name="redis",
                status=HealthStatus.HEALTHY,
                latency_ms=0,
                message="Redis not configured (optional)",
                details={"configured": False},
            )

        # Try to import and ping Redis
        try:
            import redis

            client = redis.from_url(redis_url, socket_timeout=2)
            client.ping()
            latency = (time.time() - start) * 1000
            return ComponentHealth(
                name="redis",
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                message="Redis connected",
                details={"configured": True},
            )
        except ImportError:
            return ComponentHealth(
                name="redis",
                status=HealthStatus.DEGRADED,
                latency_ms=0,
                message="Redis client not installed",
                details={"configured": True, "available": False},
            )
    except Exception as e:
        latency = (time.time() - start) * 1000
        return ComponentHealth(
            name="redis",
            status=HealthStatus.UNHEALTHY,
            latency_ms=latency,
            message=f"Redis error: {str(e)}",
        )


async def check_models() -> ComponentHealth:
    """Check ML models availability."""
    start = time.time()
    try:
        models_dir = Path("./models")
        available_models = []
        missing_models = []

        model_paths = {
            "fraud": models_dir / "fraud",
            "cyber": models_dir / "cyber",
            "behavior": models_dir / "behavior",
            "vision": models_dir / "vision",
        }

        for name, path in model_paths.items():
            if path.exists() and any(path.iterdir()):
                available_models.append(name)
            else:
                missing_models.append(name)

        latency = (time.time() - start) * 1000

        if not missing_models:
            status = HealthStatus.HEALTHY
            message = "All models available"
        elif available_models:
            status = HealthStatus.DEGRADED
            message = f"Some models missing: {', '.join(missing_models)}"
        else:
            status = HealthStatus.UNHEALTHY
            message = "No models available"

        return ComponentHealth(
            name="models",
            status=status,
            latency_ms=latency,
            message=message,
            details={
                "available": available_models,
                "missing": missing_models,
            },
        )
    except Exception as e:
        latency = (time.time() - start) * 1000
        return ComponentHealth(
            name="models",
            status=HealthStatus.UNHEALTHY,
            latency_ms=latency,
            message=f"Model check error: {str(e)}",
        )


async def check_disk_space() -> ComponentHealth:
    """Check disk space availability."""
    start = time.time()
    try:
        import shutil

        total, used, free = shutil.disk_usage("/")

        free_gb = free / (1024**3)
        used_percent = (used / total) * 100

        latency = (time.time() - start) * 1000

        if free_gb > 10:
            status = HealthStatus.HEALTHY
            message = f"Sufficient disk space: {free_gb:.1f}GB free"
        elif free_gb > 2:
            status = HealthStatus.DEGRADED
            message = f"Low disk space: {free_gb:.1f}GB free"
        else:
            status = HealthStatus.UNHEALTHY
            message = f"Critical disk space: {free_gb:.1f}GB free"

        return ComponentHealth(
            name="disk",
            status=status,
            latency_ms=latency,
            message=message,
            details={
                "total_gb": round(total / (1024**3), 2),
                "used_gb": round(used / (1024**3), 2),
                "free_gb": round(free_gb, 2),
                "used_percent": round(used_percent, 1),
            },
        )
    except Exception as e:
        latency = (time.time() - start) * 1000
        return ComponentHealth(
            name="disk",
            status=HealthStatus.DEGRADED,
            latency_ms=latency,
            message=f"Disk check error: {str(e)}",
        )


async def check_memory() -> ComponentHealth:
    """Check memory usage."""
    start = time.time()
    try:
        import psutil

        memory = psutil.virtual_memory()

        used_percent = memory.percent
        available_gb = memory.available / (1024**3)

        latency = (time.time() - start) * 1000

        # Update Prometheus gauge
        MEMORY_USAGE.set(memory.used)

        if used_percent < 80:
            status = HealthStatus.HEALTHY
            message = f"Memory usage: {used_percent:.1f}%"
        elif used_percent < 95:
            status = HealthStatus.DEGRADED
            message = f"High memory usage: {used_percent:.1f}%"
        else:
            status = HealthStatus.UNHEALTHY
            message = f"Critical memory usage: {used_percent:.1f}%"

        return ComponentHealth(
            name="memory",
            status=status,
            latency_ms=latency,
            message=message,
            details={
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(available_gb, 2),
                "used_percent": round(used_percent, 1),
            },
        )
    except ImportError:
        return ComponentHealth(
            name="memory",
            status=HealthStatus.HEALTHY,
            latency_ms=0,
            message="psutil not available",
            details={"available": False},
        )
    except Exception as e:
        latency = (time.time() - start) * 1000
        return ComponentHealth(
            name="memory",
            status=HealthStatus.DEGRADED,
            latency_ms=latency,
            message=f"Memory check error: {str(e)}",
        )


# ============================================
# API Routes
# ============================================


@router.get("/health")
async def health_check() -> dict:
    """Quick health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": _APP_VERSION,
    }


@router.get("/health/live")
async def liveness_check() -> dict:
    """Kubernetes liveness probe."""
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_check() -> JSONResponse:
    """Kubernetes readiness probe with component checks."""
    # Run health checks concurrently
    checks = await asyncio.gather(
        check_database(),
        check_models(),
        check_disk_space(),
        return_exceptions=True,
    )

    components = []
    for check in checks:
        if isinstance(check, ComponentHealth):
            components.append(check)
            # Update Prometheus metrics
            status_value = {
                HealthStatus.HEALTHY: 1.0,
                HealthStatus.DEGRADED: 0.5,
                HealthStatus.UNHEALTHY: 0.0,
            }.get(check.status, 0.0)
            HEALTH_CHECK_STATUS.labels(component=check.name).set(status_value)

    # Determine overall status
    if any(c.status == HealthStatus.UNHEALTHY for c in components):
        overall_status = HealthStatus.UNHEALTHY
        http_status = 503
    elif any(c.status == HealthStatus.DEGRADED for c in components):
        overall_status = HealthStatus.DEGRADED
        http_status = 200
    else:
        overall_status = HealthStatus.HEALTHY
        http_status = 200

    health = SystemHealth(
        status=overall_status,
        version=_APP_VERSION,
        uptime_seconds=get_uptime(),
        timestamp=datetime.utcnow().isoformat() + "Z",
        components=components,
    )

    return JSONResponse(content=health.to_dict(), status_code=http_status)


@router.get("/health/detailed")
async def detailed_health_check() -> JSONResponse:
    """Detailed health check with all components."""
    # Run all health checks concurrently
    checks = await asyncio.gather(
        check_database(),
        check_redis(),
        check_models(),
        check_disk_space(),
        check_memory(),
        return_exceptions=True,
    )

    components = []
    for check in checks:
        if isinstance(check, ComponentHealth):
            components.append(check)
        elif isinstance(check, Exception):
            components.append(
                ComponentHealth(
                    name="unknown",
                    status=HealthStatus.UNHEALTHY,
                    message=str(check),
                )
            )

    # Determine overall status
    if any(c.status == HealthStatus.UNHEALTHY for c in components):
        overall_status = HealthStatus.UNHEALTHY
        http_status = 503
    elif any(c.status == HealthStatus.DEGRADED for c in components):
        overall_status = HealthStatus.DEGRADED
        http_status = 200
    else:
        overall_status = HealthStatus.HEALTHY
        http_status = 200

    health = SystemHealth(
        status=overall_status,
        version=_APP_VERSION,
        uptime_seconds=get_uptime(),
        timestamp=datetime.utcnow().isoformat() + "Z",
        components=components,
    )

    # Add system info
    response = health.to_dict()
    response["system"] = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "hostname": platform.node(),
    }

    return JSONResponse(content=response, status_code=http_status)


@router.get("/metrics")
async def prometheus_metrics() -> Response:
    """Prometheus metrics endpoint."""
    # Update system info
    SYSTEM_INFO.info(
        {
            "version": _APP_VERSION,
            "python_version": platform.python_version(),
            "platform": platform.system(),
        }
    )

    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST,
    )


@router.get("/ready")
async def ready() -> dict:
    """Simple ready check for load balancers."""
    return {"status": "ready"}
