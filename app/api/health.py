from __future__ import annotations

from fastapi import APIRouter
from time import time

router = APIRouter()
_START = time()


@router.get("/health")
async def health() -> dict[str, object]:
    uptime = time() - _START
    return {
        "status": "ok",
        "service": "sentinelforge",
        "version": "0.1.0",
        "uptime_seconds": round(uptime, 2),
    }
