from __future__ import annotations

from datetime import datetime, timedelta
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core import settings
from app.db.models import Role, User
from app.db.session import get_db

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(settings.security.__dict__.get("access_token_expire_minutes", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(settings.security.__dict__.get("refresh_token_expire_days", 7))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def _create_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
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


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = creds.credentials
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

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")
    return user


def require_roles(*required: str) -> Callable:
    def _require(user: User = Depends(get_current_user)) -> User:
        user_roles = {role.name for role in user.roles}
        if not user_roles.intersection(required):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return _require


def ensure_role(db: Session, name: str, permissions: dict | None = None) -> Role:
    role = db.query(Role).filter(Role.name == name).first()
    if role:
        return role
    role = Role(name=name, permissions=permissions or {})
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def bootstrap_roles(db: Session) -> list[Role]:
    roles = [
        ("admin", {"admin": True}),
        ("analyst", {"read": True, "write": True}),
        ("viewer", {"read": True}),
    ]
    created = []
    for name, perms in roles:
        created.append(ensure_role(db, name, perms))
    return created


def bootstrap_admin(db: Session, username: str, password: str) -> User:
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
