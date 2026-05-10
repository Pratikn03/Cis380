from __future__ import annotations

import os
import base64
import hashlib
import hmac
import secrets
import struct
import time
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
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
from app.core.auth_audit import log_auth_event
from app.core.config import settings
from app.db.models import Role, User
from app.db.session import get_db
from app.services.audit import record_audit


def _client_meta(request: Request | None) -> tuple[str | None, str | None]:
    """Extract IP + User-Agent for auth_audit rows."""
    if request is None:
        return None, None
    ip = None
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd:
        ip = fwd.split(",")[0].strip()
    elif request.client:
        ip = request.client.host
    ua = request.headers.get("user-agent")
    return ip, ua

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


_RESET_RATE: dict[str, tuple[int, float]] = {}  # in-memory fallback for rate limiting
_RESET_RATE_LIMIT = 3       # max requests per window
_RESET_RATE_WINDOW = 3600   # 1 hour in seconds


def _check_reset_rate_limit(identifier: str) -> bool:
    """Return True if this identifier has exceeded the password-reset rate limit.

    Uses Redis when available; falls back to an in-memory counter so the
    protection works even without Redis (at the cost of per-process scope).
    Identifier is hashed before storage so we never persist raw usernames.
    """
    digest = hashlib.sha256(identifier.encode("utf-8")).hexdigest()[:24]
    client = _redis_client()
    if client is not None:
        try:
            key = f"auth:reset-rate:{digest}"
            count = int(client.incr(key))
            if count == 1:
                client.expire(key, _RESET_RATE_WINDOW)
            return count > _RESET_RATE_LIMIT
        except Exception:
            pass  # fall through to in-memory

    now = time.time()
    count, window_start = _RESET_RATE.get(digest, (0, now))
    if now - window_start > _RESET_RATE_WINDOW:
        count, window_start = 0, now
    count += 1
    _RESET_RATE[digest] = (count, window_start)
    return count > _RESET_RATE_LIMIT


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
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    ip, ua = _client_meta(request)
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        log_auth_event(
            event_type="login_failure",
            username=payload.username,
            ip_address=ip,
            user_agent=ua,
            metadata={"reason": "bad_credentials"},
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        log_auth_event(
            event_type="login_failure",
            user_id=user.id,
            username=user.username,
            ip_address=ip,
            user_agent=ua,
            metadata={"reason": "inactive"},
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")
    if user.totp_enabled:
        secret = _decrypt_secret(user.totp_secret)
        if not secret or not payload.totp_code or not _verify_totp(secret, payload.totp_code):
            log_auth_event(
                event_type="login_failure",
                user_id=user.id,
                username=user.username,
                ip_address=ip,
                user_agent=ua,
                metadata={"reason": "bad_totp"},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid TOTP code"
            )
    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    record_audit(db, action="login", target=user.username, user_id=user.id)
    log_auth_event(
        event_type="login_success",
        user_id=user.id,
        username=user.username,
        ip_address=ip,
        user_agent=ua,
        metadata={"totp_used": bool(user.totp_enabled)},
    )
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/logout", response_model=LogoutResponse)
def logout(
    request: Request,
    creds: HTTPAuthorizationCredentials = Depends(security),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LogoutResponse:
    ip, ua = _client_meta(request)
    block_access_token(creds.credentials)
    record_audit(db, action="logout", target=user.username, user_id=user.id)
    log_auth_event(
        event_type="logout",
        user_id=user.id,
        username=user.username,
        ip_address=ip,
        user_agent=ua,
    )
    return LogoutResponse(status="logged_out")


@router.post("/password-reset/request")
def password_reset_request(
    payload: PasswordResetRequest, db: Session = Depends(get_db)
) -> dict[str, Any]:
    identifier = payload.username or payload.email or ""
    if _check_reset_rate_limit(identifier):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password reset requests. Please try again later.",
        )

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
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    ip, ua = _client_meta(request)
    secret = _decrypt_secret(user.totp_secret)
    if not secret or not _verify_totp(secret, payload.code):
        log_auth_event(
            event_type="mfa_verify",
            user_id=user.id,
            username=user.username,
            ip_address=ip,
            user_agent=ua,
            metadata={"result": "fail"},
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid TOTP code")
    user.totp_enabled = True
    db.add(user)
    db.commit()
    record_audit(db, action="totp_enabled", target=user.username, user_id=user.id)
    log_auth_event(
        event_type="mfa_enroll",
        user_id=user.id,
        username=user.username,
        ip_address=ip,
        user_agent=ua,
        metadata={"result": "ok"},
    )
    return {"enabled": True}


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    from jose import JWTError, jwt
    from app.core import settings

    ip, ua = _client_meta(request)
    try:
        claims = jwt.decode(
            payload.refresh_token, settings.security.secret_key, algorithms=["HS256"]
        )
        if claims.get("type") != "refresh":
            log_auth_event(event_type="login_failure", ip_address=ip, user_agent=ua, metadata={"reason": "refresh_wrong_type"})
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user_id = claims.get("sub")
    except JWTError as exc:
        log_auth_event(event_type="login_failure", ip_address=ip, user_agent=ua, metadata={"reason": "refresh_jwt_error"})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc

    user = db.get(User, user_id)
    if not user or not user.is_active:
        log_auth_event(event_type="login_failure", user_id=user_id, ip_address=ip, user_agent=ua, metadata={"reason": "refresh_inactive"})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")
    log_auth_event(event_type="refresh", user_id=user.id, username=user.username, ip_address=ip, user_agent=ua)
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


@admin_router.get("/audit", dependencies=[Depends(require_roles("admin"))])
def admin_audit(
    event_type: str | None = None,
    user_id: str | None = None,
    since: str | None = None,
    until: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Read security events from auth_audit and (optionally) the agent_calls
    cost log. Admin-only.

    Query parameters:
      event_type: filter to one auth_audit event_type (login_success, etc.)
      user_id: filter by user
      since/until: ISO-8601 datetimes
      limit/offset: pagination (1-1000 / 0-...)
    """
    from datetime import datetime
    from app.db.models import AuthAudit, AgentCall

    if not 1 <= limit <= 1000:
        raise HTTPException(status_code=400, detail="limit must be in [1,1000]")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be >= 0")

    def _parse(ts: str | None) -> datetime | None:
        if not ts:
            return None
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"invalid datetime: {ts}") from exc

    since_dt = _parse(since)
    until_dt = _parse(until)

    q = db.query(AuthAudit)
    if event_type:
        q = q.filter(AuthAudit.event_type == event_type)
    if user_id:
        q = q.filter(AuthAudit.user_id == user_id)
    if since_dt:
        q = q.filter(AuthAudit.created_at >= since_dt)
    if until_dt:
        q = q.filter(AuthAudit.created_at <= until_dt)
    total_auth = q.count()
    rows = (
        q.order_by(AuthAudit.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    auth_events = [
        {
            "id": r.id,
            "event_type": r.event_type,
            "user_id": r.user_id,
            "username": r.username,
            "ip_address": r.ip_address,
            "user_agent": r.user_agent,
            "metadata": r.metadata_json,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]

    # Agent call summary for the same window (admin dashboards lean on it).
    aq = db.query(AgentCall)
    if user_id:
        aq = aq.filter(AgentCall.user_id == user_id)
    if since_dt:
        aq = aq.filter(AgentCall.created_at >= since_dt)
    if until_dt:
        aq = aq.filter(AgentCall.created_at <= until_dt)
    total_agent = aq.count()
    recent_agent = (
        aq.order_by(AgentCall.created_at.desc()).limit(10).all()
    )
    agent_summary = {
        "total": total_agent,
        "recent": [
            {
                "trace_id": r.trace_id,
                "user_id": r.user_id,
                "intent": r.intent,
                "answer_source": r.answer_source,
                "tool_calls": r.tool_calls,
                "latency_ms": r.latency_ms,
                "cost_usd": float(r.cost_usd) if r.cost_usd is not None else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in recent_agent
        ],
    }

    return {
        "auth_audit": {
            "total": total_auth,
            "limit": limit,
            "offset": offset,
            "events": auth_events,
        },
        "agent_calls": agent_summary,
    }


@admin_router.get("/review", dependencies=[Depends(require_roles("admin", "analyst"))])
def list_review_queue(
    status_filter: str = "pending",
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """List items waiting on analyst review (active-learning queue)."""
    from app.db.models import ReviewQueue

    if not 1 <= limit <= 500:
        raise HTTPException(status_code=400, detail="limit must be in [1,500]")
    q = db.query(ReviewQueue).filter(ReviewQueue.status == status_filter)
    total = q.count()
    rows = q.order_by(ReviewQueue.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": r.id,
                "trace_id": r.trace_id,
                "session_id": r.session_id,
                "user_id": r.user_id,
                "intent": r.intent,
                "confidence": r.confidence,
                "model_answer": r.model_answer,
                "payload": r.payload,
                "status": r.status,
                "label": r.label,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
    }


class ReviewLabelRequest(BaseModel):
    label: str
    notes: str | None = None
    status: str = "labeled"  # labeled | discarded


@admin_router.post(
    "/review/{item_id}", dependencies=[Depends(require_roles("admin", "analyst"))]
)
def label_review_item(
    item_id: int,
    payload: ReviewLabelRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Analyst applies a label and removes the item from the queue."""
    from datetime import datetime as _dt

    from app.db.models import ReviewQueue

    if payload.status not in ("labeled", "discarded"):
        raise HTTPException(status_code=400, detail="status must be labeled|discarded")
    row = db.get(ReviewQueue, item_id)
    if not row:
        raise HTTPException(status_code=404, detail="not_found")
    if row.status != "pending":
        raise HTTPException(status_code=409, detail=f"already {row.status}")
    row.label = payload.label[:64]
    row.notes = payload.notes
    row.status = payload.status
    row.reviewed_by = user.username
    row.reviewed_at = _dt.utcnow()
    db.add(row)
    db.commit()
    record_audit(
        db,
        action="review_labeled",
        target=str(row.id),
        user_id=user.id if hasattr(user, "id") else None,
    )
    return {"id": row.id, "status": row.status, "label": row.label}


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
