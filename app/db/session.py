from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


def _engine_kwargs() -> dict:
    url = settings.database.url
    kwargs: dict = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs["pool_size"] = settings.database.pool_size
        kwargs["max_overflow"] = settings.database.max_overflow
        # Hard deadline so pool exhaustion or a slow DB doesn't stall the process.
        kwargs["connect_args"] = {"connect_timeout": 10}
    return kwargs


engine = create_engine(settings.database.url, **_engine_kwargs())
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
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
