"""Simple bearer token auth dependency.

If AUTH_TOKEN env var is set, incoming requests must send:
Authorization: Bearer <AUTH_TOKEN>
If AUTH_TOKEN is unset, auth is skipped (dev mode).
"""

from __future__ import annotations

import os
from fastapi import Header, HTTPException, status


def _auth_token() -> str | None:
    return os.getenv("AUTH_TOKEN") or None


async def require_auth(authorization: str | None = Header(default=None)):
    auth_token = _auth_token()
    if not auth_token:
        return  # auth disabled
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )
    token = authorization.split(" ", 1)[1].strip()
    if token != auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    return


def check_token_query(token: str | None):
    auth_token = _auth_token()
    if not auth_token:
        return
    if token != auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
