"""FastAPI gateway for OmniChatX (pure HTTP, no Streamlit)."""
from pathlib import Path
import logging
import sys
import time

from fastapi import FastAPI, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from prometheus_client import Counter, Histogram, CONTENT_TYPE_LATEST, generate_latest

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

# Optional: reuse the app/ voice router so the backend exposes /api/voice/emotion.
try:
    from app.api.voice import router as voice_router
except Exception:  # pragma: no cover - defensive fallback if app package missing
    voice_router = None
from fastapi.responses import RedirectResponse

logger = logging.getLogger("omnichatx")
logger.setLevel(logging.INFO)
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

# CORS: allow all for demo; tighten for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
if voice_router is not None:
    app.include_router(voice_router, prefix="/api", dependencies=[Depends(require_auth)])


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    path = request.url.path
    REQUEST_COUNTER.labels(request.method, path, response.status_code).inc()
    REQUEST_LATENCY.labels(request.method, path).observe(duration)
    logger.info(
        "HTTP request",
        extra={
            "method": request.method,
            "path": path,
            "status": response.status_code,
            "duration": duration,
        },
    )
    return response


@app.get("/metrics")
def metrics():
    payload = generate_latest()
    return Response(content=payload, media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root_redirect():
    if ui_dir.exists():
        return RedirectResponse(url="/ui/")
    return {"message": "OmniChatX API. UI not found; ensure ui/ directory exists."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
