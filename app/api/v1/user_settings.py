from __future__ import annotations

import json
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.core.config import settings
from app.db.models import User

router = APIRouter(prefix="/users/me/settings", tags=["user-settings"])

_SETTINGS_MEMORY: dict[str, dict[str, Any]] = {}


class UserSettingsPayload(BaseModel):
    theme: str = Field(default="system")
    default_model: str = Field(default="auto")
    agent_token_cap: int = Field(default=2048, ge=256, le=32768)


def _redis_client():
    redis_url = os.getenv("REDIS_URL", "").strip()
    if not redis_url:
        return None
    try:
        import redis

        return redis.from_url(redis_url, socket_connect_timeout=0.5, socket_timeout=0.5)
    except Exception:
        return None


def _defaults() -> dict[str, Any]:
    return {"theme": "system", "default_model": "auto", "agent_token_cap": 2048}


@router.get("")
def get_settings(user: User = Depends(get_current_user)) -> dict[str, Any]:
    client = _redis_client()
    if client is not None:
        value = client.get(f"user_settings:{user.id}")
        if value:
            text = value.decode("utf-8") if isinstance(value, bytes) else str(value)
            return {
                "settings": _defaults() | json.loads(text),
                "backend": "redis",
                "degraded": False,
            }
        return {"settings": _defaults(), "backend": "redis", "degraded": False}
    if settings.app_env == "production":
        raise HTTPException(status_code=503, detail="Redis is required for user settings.")
    return {
        "settings": _defaults() | _SETTINGS_MEMORY.get(user.id, {}),
        "backend": "memory",
        "degraded": True,
    }


@router.put("")
def update_settings(
    payload: UserSettingsPayload, user: User = Depends(get_current_user)
) -> dict[str, Any]:
    data = payload.model_dump()
    client = _redis_client()
    if client is not None:
        client.set(f"user_settings:{user.id}", json.dumps(data), ex=60 * 60 * 24 * 365)
        return {"settings": data, "backend": "redis", "degraded": False}
    if settings.app_env == "production":
        raise HTTPException(status_code=503, detail="Redis is required for user settings.")
    _SETTINGS_MEMORY[user.id] = data
    return {"settings": data, "backend": "memory", "degraded": True}
