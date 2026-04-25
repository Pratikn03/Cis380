from __future__ import annotations

import logging

from app.core import startup


def _logger() -> logging.Logger:
    return logging.getLogger("tests.startup")


def test_initialize_dev_database_calls_ensure_schema_in_non_production(monkeypatch) -> None:
    monkeypatch.setenv("AUTO_INIT_DB", "true")
    calls = {"count": 0}

    def _fake_ensure_schema() -> None:
        calls["count"] += 1

    startup.initialize_dev_database(
        app_env="development",
        ensure_schema_fn=_fake_ensure_schema,
        logger=_logger(),
    )
    assert calls["count"] == 1


def test_initialize_dev_database_skips_in_production(monkeypatch) -> None:
    monkeypatch.setenv("AUTO_INIT_DB", "true")
    calls = {"count": 0}

    def _fake_ensure_schema() -> None:
        calls["count"] += 1

    startup.initialize_dev_database(
        app_env="production",
        ensure_schema_fn=_fake_ensure_schema,
        logger=_logger(),
    )
    assert calls["count"] == 0


def test_bootstrap_credentials_uses_dev_defaults(monkeypatch) -> None:
    monkeypatch.delenv("ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)

    username, password = startup.bootstrap_credentials(app_env="test", logger=_logger())
    assert username == "admin"
    assert password == "admin123"


def test_bootstrap_credentials_ignores_production_admin_env(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "secret")

    username, password = startup.bootstrap_credentials(app_env="production", logger=_logger())
    assert username is None
    assert password is None


def test_bootstrap_admin_user_skips_production_without_explicit_env(monkeypatch) -> None:
    monkeypatch.delenv("ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    calls = {"count": 0}

    class _DummySession:
        def __enter__(self):
            return object()

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

    def _fake_admin(_db, username: str, password: str) -> None:
        calls["count"] += 1

    startup.bootstrap_admin_user(
        app_env="production",
        ensure_schema_fn=lambda: None,
        session_factory=_DummySession,
        bootstrap_roles_fn=lambda _db: None,
        bootstrap_admin_fn=_fake_admin,
        logger=_logger(),
    )
    assert calls["count"] == 0
