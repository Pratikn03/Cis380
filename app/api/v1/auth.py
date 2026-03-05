from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])
admin_router = APIRouter(prefix="/admin", tags=["admin"])
users_router = APIRouter(prefix="/users", tags=["users"])
_bearer = HTTPBearer()


class LoginRequest(BaseModel):
    username: str
    password: str


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


def _current_user_dep(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Any:
    from app.core.auth import get_current_user

    return get_current_user(creds=creds, db=db)


def _require_admin_dep(user: Any = Depends(_current_user_dep)) -> Any:
    user_roles = {getattr(role, "name", None) for role in getattr(user, "roles", [])}
    if "admin" not in user_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    from app.core.auth import create_access_token, create_refresh_token, verify_password
    from app.db.models import User
    from app.services.audit import record_audit

    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")
    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    record_audit(db, action="login", target=user.username, user_id=user.id)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    from jose import JWTError, jwt
    from app.core.config import settings
    from app.core.auth import create_access_token, create_refresh_token
    from app.db.models import User

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
def me(user: Any = Depends(_current_user_dep)) -> dict[str, Any]:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "roles": [r.name for r in user.roles],
        "is_active": user.is_active,
    }


@admin_router.get("/users", dependencies=[Depends(_require_admin_dep)])
def list_users(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    from app.db.models import User

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


@admin_router.post("/users", dependencies=[Depends(_require_admin_dep)])
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    from app.core.auth import hash_password
    from app.db.models import Role, User
    from app.services.audit import record_audit

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


@admin_router.get("/roles", dependencies=[Depends(_require_admin_dep)])
def list_roles(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    from app.db.models import Role

    roles = db.query(Role).all()
    return [{"id": r.id, "name": r.name, "permissions": r.permissions} for r in roles]


@admin_router.post("/roles", dependencies=[Depends(_require_admin_dep)])
def create_role(payload: RoleCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    from app.core.auth import ensure_role
    from app.services.audit import record_audit

    role = ensure_role(db, payload.name, payload.permissions)
    record_audit(db, action="create_role", target=role.name)
    return {"id": role.id, "name": role.name, "permissions": role.permissions}


@admin_router.post("/bootstrap")
def bootstrap(
    payload: UserCreate,
    db: Session = Depends(get_db),
    bootstrap_token: str | None = Header(default=None, alias="X-Bootstrap-Token"),
) -> dict[str, Any]:
    from app.core.auth import bootstrap_admin
    from app.db.models import User

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
