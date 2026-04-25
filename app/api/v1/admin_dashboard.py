from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.core.config import settings
from app.db.models import AuditLog
from app.db.session import get_db
from app.services.audit import record_audit

router = APIRouter(
    prefix="/admin",
    tags=["admin-dashboard"],
    dependencies=[Depends(require_roles("admin"))],
)

_FLAGS_MEMORY: dict[str, bool] = {}


class FeatureFlagsUpdate(BaseModel):
    flags: dict[str, bool]


def _redis_client():
    redis_url = os.getenv("REDIS_URL", "").strip()
    if not redis_url:
        return None
    try:
        import redis

        return redis.from_url(redis_url, socket_connect_timeout=0.5, socket_timeout=0.5)
    except Exception:
        return None


def _manifest_path() -> Path:
    configured = os.getenv("MODEL_MANIFEST_PATH", "artifacts/release/model-manifest.json")
    return Path(configured)


@router.get("/model-registry")
def model_registry() -> dict[str, Any]:
    path = _manifest_path()
    if not path.exists():
        raise HTTPException(status_code=503, detail="Release model manifest not found.")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Could not read model manifest: {exc}"
        ) from exc
    models = manifest.get("models") if isinstance(manifest, dict) else None
    if not isinstance(models, list):
        raise HTTPException(status_code=500, detail="Model manifest has no models list.")
    return {
        "releaseName": manifest.get("releaseName"),
        "sourceCommit": manifest.get("sourceCommit"),
        "generatedAt": manifest.get("generatedAt"),
        "models": models,
        "path": str(path),
    }


@router.get("/feature-flags")
def get_feature_flags() -> dict[str, Any]:
    defaults = settings.features.model_dump()
    client = _redis_client()
    if client is not None:
        flags = defaults.copy()
        for key in defaults:
            value = client.hget("feature_flags", key)
            if value is not None:
                text = value.decode("utf-8") if isinstance(value, bytes) else str(value)
                flags[key] = text.lower() in {"1", "true", "yes", "on"}
        return {"flags": flags, "backend": "redis", "degraded": False}

    if settings.app_env == "production":
        raise HTTPException(status_code=503, detail="Redis is required for feature flags.")

    flags = defaults | _FLAGS_MEMORY
    return {"flags": flags, "backend": "memory", "degraded": True}


@router.put("/feature-flags")
def update_feature_flags(
    payload: FeatureFlagsUpdate, db: Session = Depends(get_db)
) -> dict[str, Any]:
    client = _redis_client()
    if client is not None:
        for key, value in payload.flags.items():
            client.hset("feature_flags", key, "true" if value else "false")
        backend = "redis"
        degraded = False
    else:
        if settings.app_env == "production":
            raise HTTPException(status_code=503, detail="Redis is required for feature flags.")
        _FLAGS_MEMORY.update({str(k): bool(v) for k, v in payload.flags.items()})
        backend = "memory"
        degraded = True
    record_audit(db, action="feature_flags_updated", target="feature_flags", meta=payload.flags)
    return {"flags": payload.flags, "backend": backend, "degraded": degraded}


@router.get("/audit-logs")
def audit_logs(
    limit: int = Query(100, ge=1, le=500),
    action: str | None = None,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    query = db.query(AuditLog).order_by(AuditLog.created_at.desc())
    if action:
        query = query.filter(AuditLog.action == action)
    rows = query.limit(limit).all()
    return {
        "logs": [
            {
                "id": row.id,
                "user_id": row.user_id,
                "action": row.action,
                "target": row.target,
                "meta": row.meta,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
    }
