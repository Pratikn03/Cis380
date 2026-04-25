from app.db.base import Base

__all__ = [
    "Base",
    "SessionLocal",
    "engine",
    "get_db",
]


def __getattr__(name: str):
    if name in {"SessionLocal", "engine", "get_db"}:
        from importlib import import_module

        session = import_module("app.db.session")
        return getattr(session, name)
    raise AttributeError(f"module 'app.db' has no attribute {name!r}")
