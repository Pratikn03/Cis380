from __future__ import annotations

import os
import base64
import hashlib
import hmac
import secrets
import struct
import time
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import (
    block_access_token,
    bootstrap_admin,
    create_access_token,
    create_refresh_token,
    ensure_role,
    get_current_user,
    hash_password,
    require_roles,
    verify_password,
    security,
)
from app.core.config import settings
from app.db.models import Role, User
from app.db.session import get_db
from app.services.audit import record_audit

router = APIRouter(prefix="/auth", tags=["auth"])
admin_router = APIRouter(prefix="/admin", tags=["admin"])
users_router = APIRouter(prefix="/users", tags=["users"])


class LoginRequest(BaseModel):
    username: str
    password: str
    totp_code: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserCreate(BaseModel):
    username: str
    password: str
    email: str | None = None
    roles: list[str] = []


class RoleCreate(BaseModel):
    name: str
    permissions: dict[str, Any] = {}


class LogoutResponse(BaseModel):
    status: str


class PasswordResetRequest(BaseModel):
    username: str | None = None
    email: str | None = None


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class TotpVerifyRequest(BaseModel):
    code: str


_RESET_TOKENS: dict[str, tuple[str, float]] = {}


def _redis_client():
    redis_url = os.getenv("REDIS_URL", "").strip()
    if not redis_url:
        return None
    try:
        import redis

        return redis.from_url(redis_url, socket_connect_timeout=0.5, socket_timeout=0.5)
    except Exception:
        return None


def _totp_key() -> bytes:
    digest = hashlib.sha256(settings.security.secret_key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def _encrypt_secret(secret: str) -> str:
    try:
        from cryptography.fernet import Fernet

        return Fernet(_totp_key()).encrypt(secret.encode("utf-8")).decode("ascii")
    except Exception as exc:  # pragma: no cover - dependency/environment specific
        raise HTTPException(status_code=503, detail=f"TOTP encryption unavailable: {exc}") from exc


def _decrypt_secret(value: str | None) -> str | None:
    if not value:
        return None
    try:
        from cryptography.fernet import Fernet

        return Fernet(_totp_key()).decrypt(value.encode("ascii")).decode("utf-8")
    except Exception:
        return None


def _totp_code(secret: str, step: int | None = None) -> str:
    counter = int(time.time() // 30) if step is None else step
    key = base64.b32decode(secret, casefold=True)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return f"{code % 1_000_000:06d}"


def _verify_totp(secret: str, code: str) -> bool:
    normalized = "".join(ch for ch in code if ch.isdigit())
    if len(normalized) != 6:
        return False
    current = int(time.time() // 30)
    return any(
        hmac.compare_digest(_totp_code(secret, current + delta), normalized) for delta in (-1, 0, 1)
    )


def _reset_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _store_reset_token(user_id: str, token: str, ttl_seconds: int = 900) -> None:
    digest = _reset_digest(token)
    client = _redis_client()
    if client is not None:
        client.setex(f"auth:password-reset:{digest}", ttl_seconds, user_id)
        return
    _RESET_TOKENS[digest] = (user_id, time.time() + ttl_seconds)


def _consume_reset_token(token: str) -> str | None:
    digest = _reset_digest(token)
    client = _redis_client()
    if client is not None:
        key = f"auth:password-reset:{digest}"
        user_id = client.get(key)
        if user_id:
            client.delete(key)
            return user_id.decode("utf-8") if isinstance(user_id, bytes) else str(user_id)
        return None
    value = _RESET_TOKENS.pop(digest, None)
    if not value:
        return None
    user_id, expires_at = value
    if expires_at < time.time():
        return None
    return user_id


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")
    if user.totp_enabled:
        secret = _decrypt_secret(user.totp_secret)
        if not secret or not payload.totp_code or not _verify_totp(secret, payload.totp_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid TOTP code"
            )
    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    record_audit(db, action="login", target=user.username, user_id=user.id)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/logout", response_model=LogoutResponse)
def logout(
    creds: HTTPAuthorizationCredentials = Depends(security),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LogoutResponse:
    block_access_token(creds.credentials)
    record_audit(db, action="logout", target=user.username, user_id=user.id)
    return LogoutResponse(status="logged_out")


@router.post("/password-reset/request")
def password_reset_request(
    payload: PasswordResetRequest, db: Session = Depends(get_db)
) -> dict[str, Any]:
    query = db.query(User)
    user = None
    if payload.username:
        user = query.filter(User.username == payload.username).first()
    elif payload.email:
        user = query.filter(User.email == payload.email).first()

    response: dict[str, Any] = {"status": "requested"}
    if user:
        token = secrets.token_urlsafe(32)
        _store_reset_token(user.id, token)
        record_audit(db, action="password_reset_requested", target=user.username, user_id=user.id)
        if settings.app_env != "production":
            response["reset_token"] = token
    return response


@router.post("/password-reset/confirm")
def password_reset_confirm(
    payload: PasswordResetConfirm, db: Session = Depends(get_db)
) -> dict[str, str]:
    user_id = _consume_reset_token(payload.token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token")
    user.hashed_password = hash_password(payload.new_password)
    db.add(user)
    db.commit()
    record_audit(db, action="password_reset_confirmed", target=user.username, user_id=user.id)
    return {"status": "password_updated"}


@router.post("/totp/enroll")
def totp_enroll(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict[str, Any]:
    secret = base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")
    padded_secret = secret + "=" * ((8 - len(secret) % 8) % 8)
    user.totp_secret = _encrypt_secret(padded_secret)
    user.totp_enabled = False
    db.add(user)
    db.commit()
    issuer = "Sentifargo"
    uri = f"otpauth://totp/{issuer}:{user.username}?secret={secret}&issuer={issuer}&algorithm=SHA1&digits=6&period=30"
    record_audit(db, action="totp_enroll_started", target=user.username, user_id=user.id)
    return {"secret": secret, "otpauth_uri": uri, "enabled": False}


@router.post("/totp/verify")
def totp_verify(
    payload: TotpVerifyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    secret = _decrypt_secret(user.totp_secret)
    if not secret or not _verify_totp(secret, payload.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid TOTP code")
    user.totp_enabled = True
    db.add(user)
    db.commit()
    record_audit(db, action="totp_enabled", target=user.username, user_id=user.id)
    return {"enabled": True}


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    from jose import JWTError, jwt
    from app.core import settings

    try:
        claims = jwt.decode(
            payload.refresh_token, settings.security.secret_key, algorithms=["HS256"]
        )
        if claims.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user_id = claims.get("sub")
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@users_router.get("/me")
def me(user: User = Depends(get_current_user)) -> dict[str, Any]:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "roles": [r.name for r in user.roles],
        "is_active": user.is_active,
    }


@admin_router.get("/users", dependencies=[Depends(require_roles("admin"))])
def list_users(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "roles": [r.name for r in u.roles],
            "is_active": u.is_active,
        }
        for u in users
    ]


@admin_router.post("/users", dependencies=[Depends(require_roles("admin"))])
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    for role_name in payload.roles:
        role = db.query(Role).filter(Role.name == role_name).first()
        if role:
            user.roles.append(role)
    db.add(user)
    db.commit()
    db.refresh(user)
    record_audit(db, action="create_user", target=user.username)
    return {"id": user.id, "username": user.username, "roles": [r.name for r in user.roles]}


@admin_router.get("/roles", dependencies=[Depends(require_roles("admin"))])
def list_roles(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    roles = db.query(Role).all()
    return [{"id": r.id, "name": r.name, "permissions": r.permissions} for r in roles]


@admin_router.post("/roles", dependencies=[Depends(require_roles("admin"))])
def create_role(payload: RoleCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    role = ensure_role(db, payload.name, payload.permissions)
    record_audit(db, action="create_role", target=role.name)
    return {"id": role.id, "name": role.name, "permissions": role.permissions}


@admin_router.post("/bootstrap")
def bootstrap(
    payload: UserCreate,
    db: Session = Depends(get_db),
    bootstrap_token: str | None = Header(default=None, alias="X-Bootstrap-Token"),
) -> dict[str, Any]:
    expected_token = os.getenv("BOOTSTRAP_TOKEN")
    if not expected_token:
        raise HTTPException(status_code=403, detail="Bootstrap disabled")
    if bootstrap_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bootstrap token"
        )
    if db.query(User).count() > 0:
        raise HTTPException(status_code=400, detail="Bootstrap already completed")
    admin = bootstrap_admin(db, payload.username, payload.password)
    return {"id": admin.id, "username": admin.username}
