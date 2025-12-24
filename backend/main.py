"""FastAPI gateway for OmniChatX (pure HTTP, no Streamlit)."""

from __future__ import annotations

from pathlib import Path
import importlib.util
import logging
import os
import platform
import sys
import time

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from prometheus_client import Counter, Histogram

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Pre-import torch/torchvision if available.
# This avoids a known macOS hang when XGBoost is imported before Torch in the same process.
try:  # pragma: no cover
    import torch  # noqa: F401
    import torchvision  # noqa: F401
except Exception:
    pass

from api.deps import require_auth
from api.routes import chat, rag, recommend, behavior, fraud, cyber, vision

_app_risk_router = None
_app_monitor_router = None
_app_voice_router = None
_app_rag_router = None
_app_brand_router = None
_app_stt_router = None
_app_vision_temporal_router = None

# Optional: reuse selected app/ routers so `backend.main` can be the single runtime.
# Import each router independently so an optional module doesn't disable the whole stack.
try:  # pragma: no cover
    from app.api.risk import router as _app_risk_router
except Exception as exc:  # pragma: no cover
    logging.getLogger("omnichatx").warning("app.api.risk router unavailable: %s", exc)
    _app_risk_router = None

try:  # pragma: no cover
    from app.api.monitor import router as _app_monitor_router
except Exception as exc:  # pragma: no cover
    logging.getLogger("omnichatx").warning("app.api.monitor router unavailable: %s", exc)
    _app_monitor_router = None

try:  # pragma: no cover
    from app.api.voice import router as _app_voice_router
except Exception as exc:  # pragma: no cover
    logging.getLogger("omnichatx").warning("app.api.voice router unavailable: %s", exc)
    _app_voice_router = None

try:  # pragma: no cover
    from app.api.rag import router as _app_rag_router
except Exception as exc:  # pragma: no cover
    logging.getLogger("omnichatx").warning("app.api.rag router unavailable: %s", exc)
    _app_rag_router = None

try:  # pragma: no cover
    from app.api.brand import router as _app_brand_router
except Exception as exc:  # pragma: no cover
    logging.getLogger("omnichatx").warning("app.api.brand router unavailable: %s", exc)
    _app_brand_router = None

try:  # pragma: no cover
    from app.api.stt import router as _app_stt_router
except Exception as exc:  # pragma: no cover
    logging.getLogger("omnichatx").warning("app.api.stt router unavailable: %s", exc)
    _app_stt_router = None

try:  # pragma: no cover
    from app.api.vision_temporal import router as _app_vision_temporal_router
except Exception as exc:  # pragma: no cover
    logging.getLogger("omnichatx").warning("app.api.vision_temporal router unavailable: %s", exc)
    _app_vision_temporal_router = None

try:  # pragma: no cover
    from app.core import health_router as _health_router
except Exception as exc:  # pragma: no cover
    logging.getLogger("omnichatx").warning("app.core.health router unavailable: %s", exc)
    _health_router = None
from fastapi.responses import RedirectResponse

logger = logging.getLogger("omnichatx")
_log_level_name = (os.getenv("LOG_LEVEL") or "INFO").upper()
logger.setLevel(getattr(logging, _log_level_name, logging.INFO))
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",
            "%Y-%m-%dT%H:%M:%S",
        )
    )
    logger.addHandler(handler)

REQUEST_COUNTER = Counter(
    "omnichatx_http_requests_total",
    "Total HTTP requests handled by OmniChatX API",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "omnichatx_http_request_latency_seconds",
    "Latency of HTTP requests handled by OmniChatX API",
    ["method", "path"],
)


app = FastAPI(title="OmniChatX API", version="0.2")

def _parse_cors_origins() -> list[str]:
    raw = (os.getenv("CORS_ORIGINS") or "*").strip()
    if not raw or raw == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


# CORS: allow all for demo; configure via CORS_ORIGINS in production (comma-separated).
_cors_origins = _parse_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_cors_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static UI under /ui (optional)
ui_dir = Path(__file__).resolve().parents[1] / "ui"
if ui_dir.exists():
    app.mount("/ui", StaticFiles(directory=ui_dir, html=True), name="ui")

# Include API routers
app.include_router(chat.router)
app.include_router(rag.router)
app.include_router(recommend.router)
app.include_router(behavior.router)
app.include_router(fraud.router)
app.include_router(cyber.router)
app.include_router(vision.router)
if _health_router is not None:
    # Production-grade health + readiness + metrics endpoints:
    #   /health, /health/live, /health/ready, /health/detailed, /metrics, /ready
    app.include_router(_health_router)
if _app_risk_router is not None:
    app.include_router(_app_risk_router, prefix="/api", dependencies=[Depends(require_auth)])
if _app_monitor_router is not None:
    app.include_router(_app_monitor_router, prefix="/api", dependencies=[Depends(require_auth)])
if _app_voice_router is not None:
    app.include_router(_app_voice_router, prefix="/api", dependencies=[Depends(require_auth)])
if _app_rag_router is not None:
    app.include_router(_app_rag_router, prefix="/api", dependencies=[Depends(require_auth)])
if _app_brand_router is not None:
    app.include_router(_app_brand_router, dependencies=[Depends(require_auth)])
if _app_stt_router is not None:
    app.include_router(_app_stt_router, prefix="/api", dependencies=[Depends(require_auth)])
if _app_vision_temporal_router is not None:
    app.include_router(_app_vision_temporal_router, prefix="/api", dependencies=[Depends(require_auth)])


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    path = request.url.path
    REQUEST_COUNTER.labels(request.method, path, response.status_code).inc()
    REQUEST_LATENCY.labels(request.method, path).observe(duration)
    logger.info(
        "%s %s -> %s (%.3fs)",
        request.method,
        path,
        response.status_code,
        duration,
    )
    return response


def _module_available(module_name: str) -> bool:
    """Return True if a module can be imported (without importing it).

    Using `find_spec` avoids importing heavy packages (torch, faiss, etc.) during
    health checks and keeps startup fast.
    """

    try:
        return importlib.util.find_spec(module_name) is not None
    except Exception:  # pragma: no cover
        return False


@app.get("/api/health")
def api_health():
    """Richer health endpoint for the Streamlit dashboard.

    Contract:
      {status, service, version, python, platform, optional_features}

    optional_features reports "availability" only (installed/importable), not whether
    a model/index has been built.
    """

    optional_features = {
        # Streamlit WebRTC support.
        "webrtc": _module_available("streamlit_webrtc") and _module_available("av"),
        # Speech-to-text support.
        "stt": _module_available("faster_whisper") or _module_available("whisper"),
        # Multimodal embedding support.
        "clip": _module_available("transformers") and _module_available("torch"),
        # Similarity index support.
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
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "optional_features": optional_features,
    }


@app.get("/")
def root_redirect():
    if ui_dir.exists():
        return RedirectResponse(url="/ui/")
    return {"message": "OmniChatX API. UI not found; ensure ui/ directory exists."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
