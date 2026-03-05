from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

LOCAL_SQLITE_URL = "sqlite:///./data/Sentifargo.db"


def _database_url() -> str:
    url = settings.database.url
    try:
        parsed = make_url(url)
    except Exception:
        return url

    if parsed.drivername.startswith("sqlite"):
        return url

    host = (parsed.host or "").strip().lower()
    allow_docker_host = os.getenv("ALLOW_DOCKER_DATABASE_URL", "false").lower() in {
        "1",
        "true",
        "yes",
    }
    if host in {"postgres", "db", "database"} and not allow_docker_host:
        return LOCAL_SQLITE_URL
    return url


def _engine_kwargs() -> dict:
    url = _database_url()
    kwargs: dict = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs["pool_size"] = settings.database.pool_size
        kwargs["max_overflow"] = settings.database.max_overflow
    return kwargs


engine = create_engine(_database_url(), **_engine_kwargs())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def ensure_schema() -> None:
    """Create missing DB tables for local/dev environments."""
    from app.db.base import Base
    import app.db.models  # noqa: F401  # ensure models are registered on Base metadata

    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
