"""
==============================================================================
OMNICHATX API - Main FastAPI Application Entry Point
==============================================================================
Author: Pratik Niroula
Project: Sentifargo (Sentifargo)

WHAT THIS FILE DOES:
--------------------
This is the main entry point for the FastAPI backend server. It:
1. Creates the FastAPI web application
2. Sets up API routes for different ML services (fraud, cyber, vision, etc.)
3. Configures CORS (Cross-Origin Resource Sharing) for web access
4. Serves the React frontend as static files
5. Provides health check endpoints for monitoring

HOW TO RUN:
-----------
    uvicorn app.main:app --reload --port 8000

Then visit: http://localhost:8000/ui for the web interface
            http://localhost:8000/docs for API documentation

ARCHITECTURE:
-------------
    [Frontend React App] <---> [This FastAPI Server] <---> [ML Models/Services]
                                      |
                                      v
                              [Database/Storage]
==============================================================================
"""

from __future__ import annotations

# ==============================================================================
# IMPORTS - External libraries and internal modules
# ==============================================================================
from pathlib import Path
import importlib.util
import logging
import os
import platform
import sys
import time

# FastAPI - Modern web framework for building APIs
from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles  # Serves React frontend files
from prometheus_client import Counter, Histogram  # Metrics for monitoring
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

# ==============================================================================
# PATH SETUP - Ensure Python can find our project modules
# ==============================================================================
# ROOT = Project root directory (one level up from app/)
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# SRC_DIR = Contains ML model code (src/fraud, src/cyber, etc.)
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# ==============================================================================
# PYTORCH PRE-IMPORT FIX
# ==============================================================================
# On macOS, importing XGBoost before PyTorch can cause the app to hang.
# By importing torch/torchvision first, we avoid this known issue.
try:  # pragma: no cover
    import torch  # noqa: F401
    import torchvision  # noqa: F401
except Exception:
    pass  # It's okay if PyTorch is not installed

# ==============================================================================
# IMPORT API ROUTES - Each route handles a specific ML service
# ==============================================================================
from app.core import settings, setup_production_middleware  # noqa: E402
from app.legacy.api.deps import require_auth  # noqa: E402
from app.legacy.api.routes import behavior, chat, cyber, fraud, rag, recommend, vision  # noqa: E402

# Initialize optional router variables (set to None if module not available)
_app_risk_router = None       # Unified risk scoring
_app_monitor_router = None    # System monitoring
_app_voice_router = None      # Voice/audio analysis
_app_rag_router = None        # Document Q&A (Retrieval Augmented Generation)
_app_dsa_rag_router = None    # DSA RAG (offline-first)
_app_brand_router = None      # Brand/logo detection
_app_stt_router = None        # Speech-to-text
_app_vision_temporal_router = None  # Video/temporal analysis

# ==============================================================================
# OPTIONAL ROUTER IMPORTS
# ==============================================================================
# Each router is imported separately with error handling.
# This ensures one missing module doesn't break the entire application.

# Risk Router - Provides unified fraud/cyber/behavior risk scoring
try:  # pragma: no cover
    from app.api.risk import router as _app_risk_router
except Exception as exc:  # pragma: no cover
    logging.getLogger("omnichatx").warning("app.api.risk router unavailable: %s", exc)
    _app_risk_router = None

# Monitor Router - System health and performance monitoring
try:  # pragma: no cover
    from app.api.monitor import router as _app_monitor_router
except Exception as exc:  # pragma: no cover
    logging.getLogger("omnichatx").warning("app.api.monitor router unavailable: %s", exc)
    _app_monitor_router = None

# Voice Router - Voice emotion detection and audio analysis
try:  # pragma: no cover
    from app.api.voice import router as _app_voice_router
except Exception as exc:  # pragma: no cover
    logging.getLogger("omnichatx").warning("app.api.voice router unavailable: %s", exc)
    _app_voice_router = None

# RAG Router - Upload documents and ask questions about them
try:  # pragma: no cover
    from app.api.rag import router as _app_rag_router
except Exception as exc:  # pragma: no cover
    logging.getLogger("omnichatx").warning("app.api.rag router unavailable: %s", exc)
    _app_rag_router = None

# DSA RAG Router - Offline-first DSA document Q&A
try:  # pragma: no cover
    from app.api.dsa_rag import router as _app_dsa_rag_router
    from app.rag_dsa.config import settings as _dsa_rag_settings
    from app.rag_dsa.ingest import ensure_index as _dsa_rag_ensure_index
except Exception as exc:  # pragma: no cover
    logging.getLogger("omnichatx").warning("app.api.dsa_rag router unavailable: %s", exc)
    _app_dsa_rag_router = None
    _dsa_rag_settings = None
    _dsa_rag_ensure_index = None

# Brand Router - Logo and brand detection in images
try:  # pragma: no cover
    from app.api.brand import router as _app_brand_router
except Exception as exc:  # pragma: no cover
    logging.getLogger("omnichatx").warning("app.api.brand router unavailable: %s", exc)
    _app_brand_router = None

# STT Router - Speech-to-Text transcription
try:  # pragma: no cover
    from app.api.stt import router as _app_stt_router
except Exception as exc:  # pragma: no cover
    logging.getLogger("omnichatx").warning("app.api.stt router unavailable: %s", exc)
    _app_stt_router = None

# Vision Temporal Router - Video frame analysis over time
try:  # pragma: no cover
    from app.api.vision_temporal import router as _app_vision_temporal_router
except Exception as exc:  # pragma: no cover
    logging.getLogger("omnichatx").warning("app.api.vision_temporal router unavailable: %s", exc)
    _app_vision_temporal_router = None

# Health Router - Production-grade health checks
try:  # pragma: no cover
    from app.core import health_router as _health_router
except Exception as exc:  # pragma: no cover
    logging.getLogger("omnichatx").warning("app.core.health router unavailable: %s", exc)
    _health_router = None

from fastapi.responses import RedirectResponse  # noqa: E402

# ==============================================================================
# LOGGING SETUP
# ==============================================================================
# Create a logger for this application with configurable log level
logger = logging.getLogger("omnichatx")
_log_level_name = (os.getenv("LOG_LEVEL") or "INFO").upper()  # Default: INFO
logger.setLevel(getattr(logging, _log_level_name, logging.INFO))

# Add a console handler if none exists (prints logs to terminal)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",  # Format: timestamp level name message
            "%Y-%m-%dT%H:%M:%S",  # Timestamp format: 2024-01-15T10:30:45
        )
    )
    logger.addHandler(handler)

# ==============================================================================
# PROMETHEUS METRICS - Track API usage and performance
# ==============================================================================
# Counter: Counts total number of HTTP requests (increments only)
REQUEST_COUNTER = Counter(
    "omnichatx_http_requests_total",        # Metric name
    "Total HTTP requests handled by OmniChatX API",  # Description
    ["method", "path", "status"],           # Labels: GET/POST, /api/fraud, 200/404
)

# Histogram: Tracks request duration distribution
REQUEST_LATENCY = Histogram(
    "omnichatx_http_request_latency_seconds",
    "Latency of HTTP requests handled by OmniChatX API",
    ["method", "path"],
)

# ==============================================================================
# CREATE FASTAPI APPLICATION
# ==============================================================================
app = FastAPI(
    title="OmniChatX API",  # Shown in API docs at /docs
    version="0.2",          # API version
)

# ==============================================================================
# PRODUCTION MIDDLEWARE - Security headers, rate limits, CORS, request IDs
# ==============================================================================
setup_production_middleware(
    app,
    cors_origins=settings.security.cors_origins,
    rate_limit_enabled=settings.security.rate_limit_enabled,
    rate_limit_requests=settings.security.rate_limit_requests,
    rate_limit_window=settings.security.rate_limit_window,
    max_request_size=settings.max_request_size,
)

# Optional hardening: host validation + HTTPS redirect in production.
_allowed_hosts = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "*").split(",") if h.strip()]
if _allowed_hosts != ["*"]:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=_allowed_hosts)
if os.getenv("FORCE_HTTPS", "false").lower() == "true":
    app.add_middleware(HTTPSRedirectMiddleware)

# ==============================================================================
# STATIC FILES - Serve the React frontend
# ==============================================================================
# The React app is built to ui-web/frontend/dist/
# This makes it available at http://localhost:8000/ui/
ui_dir = Path(__file__).resolve().parents[1] / "ui-web" / "frontend" / "dist"
if ui_dir.exists():
    app.mount("/ui", StaticFiles(directory=ui_dir, html=True), name="ui")

# ==============================================================================
# REGISTER API ROUTERS - Each router handles specific endpoints
# ==============================================================================
# Legacy routers (no authentication required for demo)
app.include_router(chat.router)      # /chat - Chatbot conversations
app.include_router(rag.router)       # /rag - Document Q&A
app.include_router(recommend.router) # /recommend - Recommendations
app.include_router(behavior.router)  # /behavior - User behavior analysis
app.include_router(fraud.router)     # /fraud - Fraud detection
app.include_router(cyber.router)     # /cyber - Cybersecurity threats
app.include_router(vision.router)    # /vision - Image analysis

# Health check router (production monitoring)
if _health_router is not None:
    # Provides: /health, /health/live, /health/ready, /health/detailed, /metrics
    app.include_router(_health_router)

# New routers with authentication (protected endpoints)
if _app_risk_router is not None:
    app.include_router(_app_risk_router, prefix="/api", dependencies=[Depends(require_auth)])
if _app_monitor_router is not None:
    app.include_router(_app_monitor_router, prefix="/api", dependencies=[Depends(require_auth)])
if _app_voice_router is not None:
    app.include_router(_app_voice_router, prefix="/api", dependencies=[Depends(require_auth)])
if _app_rag_router is not None:
    app.include_router(_app_rag_router, prefix="/api", dependencies=[Depends(require_auth)])
if _app_dsa_rag_router is not None:
    app.include_router(_app_dsa_rag_router, prefix="/api", dependencies=[Depends(require_auth)])
if _app_brand_router is not None:
    app.include_router(_app_brand_router, dependencies=[Depends(require_auth)])
if _app_stt_router is not None:
    app.include_router(_app_stt_router, prefix="/api", dependencies=[Depends(require_auth)])
if _app_vision_temporal_router is not None:
    app.include_router(
        _app_vision_temporal_router, prefix="/api", dependencies=[Depends(require_auth)]
    )

# ==============================================================================
# STARTUP TASKS - Best-effort index build for DSA RAG
# ==============================================================================
if _dsa_rag_ensure_index is not None:
    @app.on_event("startup")
    def _dsa_rag_startup() -> None:
        if _dsa_rag_settings is None or not _dsa_rag_settings.AUTO_INGEST:
            return
        try:
            _dsa_rag_ensure_index()
        except Exception as exc:  # pragma: no cover
            logger.warning("DSA RAG auto-ingest skipped: %s", exc)


# ==============================================================================
# REQUEST LOGGING MIDDLEWARE
# ==============================================================================
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware that logs every HTTP request and tracks metrics.
    
    This runs BEFORE and AFTER every API call:
    1. Records start time
    2. Processes the actual request
    3. Logs the result and duration
    4. Updates Prometheus metrics
    
    Example log output:
        2024-01-15T10:30:45 INFO omnichatx GET /api/health -> 200 (0.005s)
    """
    start = time.time()                    # Start timing
    response = await call_next(request)    # Process the request
    duration = time.time() - start         # Calculate duration
    
    path = request.url.path
    
    # Update Prometheus metrics
    REQUEST_COUNTER.labels(request.method, path, response.status_code).inc()
    REQUEST_LATENCY.labels(request.method, path).observe(duration)
    
    # Log the request (optional; set LOG_REQUESTS=true to enable)
    if os.getenv("LOG_REQUESTS", "false").lower() == "true":
        logger.info(
            "%s %s -> %s (%.3fs)",    # Format string
            request.method,           # GET, POST, etc.
            path,                     # /api/fraud
            response.status_code,     # 200, 404, etc.
            duration,                 # Time in seconds
        )
    return response


# ==============================================================================
# HELPER FUNCTION - Check if a Python module is installed
# ==============================================================================
def _module_available(module_name: str) -> bool:
    """
    Check if a Python module can be imported without actually importing it.
    
    This is faster than trying to import because:
    - Some modules (torch, faiss) take seconds to import
    - We just want to know if they're installed
    
    Args:
        module_name: Name of the module (e.g., "torch", "faiss")
        
    Returns:
        bool: True if module is installed, False otherwise
        
    Example:
        >>> _module_available("torch")
        True  # If PyTorch is installed
    """
    try:
        return importlib.util.find_spec(module_name) is not None
    except Exception:  # pragma: no cover
        return False


# ==============================================================================
# API ENDPOINTS
# ==============================================================================
@app.get("/api/health")
def api_health():
    """
    Health check endpoint that returns system status and capabilities.
    
    Used by:
    - Monitoring systems (Kubernetes, Docker health checks)
    - Frontend to display system status
    - DevOps to verify deployment
    
    Returns:
        dict: System status including:
            - status: "ok" if healthy
            - service: Service name
            - version: API version
            - python: Python version info
            - platform: OS information
            - optional_features: Available ML capabilities
    
    Example response:
        {
            "status": "ok",
            "service": "omnichatx",
            "version": "0.2",
            "python": {"version": "3.11.0", "implementation": "CPython"},
            "platform": {"system": "Darwin", "release": "23.0.0", "machine": "arm64"},
            "optional_features": {
                "webrtc": true,
                "stt": true,
                "clip": false,
                "faiss": true
            }
        }
    """
    # Check which optional ML features are available
    optional_features = {
        # WebRTC: Real-time video/audio streaming
        "webrtc": _module_available("streamlit_webrtc") and _module_available("av"),
        # STT: Speech-to-Text transcription
        "stt": _module_available("faster_whisper") or _module_available("whisper"),
        # CLIP: Multimodal image-text embeddings
        "clip": _module_available("transformers") and _module_available("torch"),
        # FAISS: Fast similarity search for embeddings
        "faiss": _module_available("faiss") or _module_available("faiss_cpu"),
    }

    return {
        "status": "ok",
        "service": "omnichatx",
        "version": app.version,
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
        },
        "platform": {
            "system": platform.system(),      # "Darwin" (macOS), "Linux", "Windows"
            "release": platform.release(),    # OS version
            "machine": platform.machine(),    # "arm64", "x86_64"
        },
        "optional_features": optional_features,
    }


@app.get("/")
def root_redirect():
    """
    Root endpoint - Redirects to the UI or returns API info.
    
    Behavior:
    - If UI is built: Redirects to /ui/ (React frontend)
    - If UI not built: Returns a simple JSON message
    """
    if ui_dir.exists():
        return RedirectResponse(url="/ui/")
    return {"message": "OmniChatX API. UI not found; ensure ui/ directory exists."}


# ==============================================================================
# MAIN ENTRY POINT - Run with: python app/main.py
# ==============================================================================
if __name__ == "__main__":
    import uvicorn
    
    # Start the server on all interfaces (0.0.0.0) port 8000
    # This allows access from other devices on the network
    uvicorn.run(app, host="0.0.0.0", port=8000)
