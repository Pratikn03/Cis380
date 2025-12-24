"""Compatibility entrypoint.

Use `uvicorn app.main:app` as the canonical FastAPI entrypoint.

The gateway implementation lives in `backend/main.py`. This module re-exports the
same FastAPI app so imports remain stable across scripts, tests, and deployments.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.main import app  # noqa: F401, E402
