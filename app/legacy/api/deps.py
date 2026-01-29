"""Legacy bearer/JWT auth dependency.

- If AUTH_TOKEN is set, Bearer <AUTH_TOKEN> is accepted (legacy).
- Otherwise, a valid JWT access token is required.
- AUTH_BYPASS=true is allowed in non-production for tests/dev.
"""

from __future__ import annotations

import os

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core import settings
from app.db.models import User
from app.db.session import SessionLocal, get_db


def _auth_token() -> str | None:
    return os.getenv("AUTH_TOKEN") or None


def _extract_bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    if not authorization.lower().startswith("bearer "):
        return None
    return authorization.split(" ", 1)[1].strip()


def _verify_jwt(token: str, db: Session) -> None:
    try:
        claims = jwt.decode(token, settings.security.secret_key, algorithms=["HS256"])
        if claims.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user_id = claims.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")


async def require_auth(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    if os.getenv("AUTH_BYPASS", "false").lower() == "true" and settings.app_env != "production":
        return
    token = _extract_bearer(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    auth_token = _auth_token()
    if auth_token and token == auth_token:
        return

    _verify_jwt(token, db)
    return


def check_token_query(token: str | None):
    if os.getenv("AUTH_BYPASS", "false").lower() == "true" and settings.app_env != "production":
        return
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )
    auth_token = _auth_token()
    if auth_token and token == auth_token:
        return
    with SessionLocal() as db:
        _verify_jwt(token, db)
