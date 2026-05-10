from __future__ import annotations

import base64
import binascii
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
import time
from typing import TYPE_CHECKING, Callable

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal

if TYPE_CHECKING:
    from app.db.models import Role, User

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(settings.security.__dict__.get("access_token_expire_minutes", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(settings.security.__dict__.get("refresh_token_expire_days", 7))
PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_HASH_ITERATIONS = int(os.getenv("PASSWORD_HASH_ITERATIONS", "30000"))
PASSWORD_SALT_BYTES = 16

security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = os.urandom(PASSWORD_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_HASH_ITERATIONS)
    return (
        f"{PASSWORD_SCHEME}${PASSWORD_HASH_ITERATIONS}$"
        f"{base64.b64encode(salt).decode('ascii')}$"
        f"{base64.b64encode(digest).decode('ascii')}"
    )


def verify_password(password: str, hashed_password: str) -> bool:
    if hashed_password.startswith(f"{PASSWORD_SCHEME}$"):
        return _verify_pbkdf2(password, hashed_password)
    return _verify_legacy_passlib(password, hashed_password)


def _verify_pbkdf2(password: str, encoded_hash: str) -> bool:
    try:
        _, rounds_str, salt_b64, digest_b64 = encoded_hash.split("$", 3)
        rounds = int(rounds_str)
        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected = base64.b64decode(digest_b64.encode("ascii"))
    except (ValueError, binascii.Error):
        return False

    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, rounds)
    return hmac.compare_digest(actual, expected)


def _verify_legacy_passlib(password: str, hashed_password: str) -> bool:
    """
    Backward-compatibility path for existing passlib hashes.
    If passlib/bcrypt backend support is unavailable, treat as non-match.
    """
    try:
        from passlib.context import CryptContext

        legacy_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")
        return legacy_context.verify(password, hashed_password)
    except Exception:
        return False


def _get_db():
    from app.db.session import get_db as _get_db_dependency

    yield from _get_db_dependency()


def _auth_token() -> str | None:
    return settings.security.auth_token or os.getenv("AUTH_TOKEN") or None


_BYPASS_BLOCKED_ENVS = {"production", "staging", "qa"}


def _auth_bypass_enabled() -> bool:
    return os.getenv("AUTH_BYPASS", "false").lower() == "true" and settings.app_env not in _BYPASS_BLOCKED_ENVS


def _extract_bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    if not authorization.lower().startswith("bearer "):
        return None
    return authorization.split(" ", 1)[1].strip()


def _is_token_blocked(token: str) -> bool:
    redis_url = os.getenv("REDIS_URL", "").strip()
    if not redis_url:
        return False
    try:
        import redis

        client = redis.from_url(redis_url, socket_connect_timeout=0.2, socket_timeout=0.2)
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        return bool(client.exists(f"auth:blocked:{digest}"))
    except Exception:
        return False


def block_access_token(token: str, ttl_seconds: int | None = None) -> None:
    redis_url = os.getenv("REDIS_URL", "").strip()
    if not redis_url:
        return
    try:
        import redis

        ttl = ttl_seconds or max(60, ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        client = redis.from_url(redis_url, socket_connect_timeout=0.5, socket_timeout=0.5)
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        client.setex(f"auth:blocked:{digest}", ttl, str(int(time.time())))
    except Exception:
        return


def _create_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.security.secret_key, algorithm=ALGORITHM)


def create_access_token(user_id: str) -> str:
    return _create_token(
        {"sub": user_id, "type": "access"},
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: str) -> str:
    return _create_token(
        {"sub": user_id, "type": "refresh"},
        timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )


def _decode_token(token: str) -> dict:
    return jwt.decode(token, settings.security.secret_key, algorithms=[ALGORITHM])


def verify_access_token(token: str, db: Session) -> "User":
    if _is_token_blocked(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
    try:
        payload = _decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc

    from app.db.models import User

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")
    return user


async def require_auth(
    authorization: str | None = Header(default=None),
    db: Session = Depends(_get_db),
) -> None:
    if _auth_bypass_enabled():
        return

    token = _extract_bearer(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    auth_token = _auth_token()
    if auth_token and hmac.compare_digest(token, auth_token):
        return

    verify_access_token(token, db)


def check_token_query(token: str | None) -> None:
    if _auth_bypass_enabled():
        return
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )
    auth_token = _auth_token()
    if auth_token and hmac.compare_digest(token, auth_token):
        return
    with SessionLocal() as db:
        verify_access_token(token, db)


class _BypassUser:
    """Stand-in returned by get_current_user when AUTH_BYPASS is enabled in
    dev. Mimics just enough of the real User model that role checks pass."""

    id = "auth-bypass"
    username = "dev-bypass"
    is_active = True

    class _AllRoles:
        def __init__(self) -> None:
            self.name = "admin"

    roles = [_AllRoles()]


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(_get_db),
) -> "User":
    if _auth_bypass_enabled():
        return _BypassUser()  # type: ignore[return-value]
    if creds is None or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )
    return verify_access_token(creds.credentials, db)


def require_roles(*required: str) -> Callable:
    def _require(user: "User" = Depends(get_current_user)) -> "User":
        if _auth_bypass_enabled():
            return user
        user_roles = {role.name for role in user.roles}
        if not user_roles.intersection(required):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return _require


def require_role(role: str) -> Callable:
    """Singular alias for ``require_roles(role)``."""
    return require_roles(role)


def ensure_role(db: Session, name: str, permissions: dict | None = None) -> "Role":
    from app.db.models import Role

    role = db.query(Role).filter(Role.name == name).first()
    if role:
        return role
    role = Role(name=name, permissions=permissions or {})
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def bootstrap_roles(db: Session) -> list["Role"]:
    roles = [
        ("admin", {"admin": True}),
        ("analyst", {"read": True, "write": True}),
        ("viewer", {"read": True}),
    ]
    created = []
    for name, perms in roles:
        created.append(ensure_role(db, name, perms))
    return created


def bootstrap_admin(db: Session, username: str, password: str) -> "User":
    from app.db.models import User

    user = db.query(User).filter(User.username == username).first()
    if user:
        return user
    admin_role = ensure_role(db, "admin", {"admin": True})
    user = User(username=username, email=None, hashed_password=hash_password(password))
    user.roles.append(admin_role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
