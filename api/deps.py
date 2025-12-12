"""Simple bearer token auth dependency.

If AUTH_TOKEN env var is set, incoming requests must send:
Authorization: Bearer <AUTH_TOKEN>
If AUTH_TOKEN is unset, auth is skipped (dev mode).
"""
from __future__ import annotations

import os
from fastapi import Header, HTTPException, status


AUTH_TOKEN = os.getenv("AUTH_TOKEN")


async def require_auth(authorization: str | None = Header(default=None)):
    if not AUTH_TOKEN:
        return  # auth disabled
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )
    token = authorization.split(" ", 1)[1].strip()
    if token != AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
    )
    return


def check_token_query(token: str | None):
    if not AUTH_TOKEN:
        return
    if token != AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
