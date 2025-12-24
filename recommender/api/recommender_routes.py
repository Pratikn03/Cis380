"""Placeholder FastAPI routes for hybrid recommender."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/hybrid-recommend", tags=["hybrid-recommend"])


@router.get("/ping")
def ping():
    return {"status": "ok", "detail": "hybrid recommender stub"}
