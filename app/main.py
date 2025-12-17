"""Compatibility entrypoint.

Use `uvicorn app.main:app` as the canonical FastAPI entrypoint.

The gateway implementation lives in `backend/main.py`. This module re-exports the
same FastAPI app so imports remain stable across scripts, tests, and deployments.
"""

from backend.main import app  # noqa: F401
