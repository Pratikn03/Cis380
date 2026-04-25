from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import DatabaseSettings, RedisSettings, SecuritySettings, Settings
from app.main import app
import app.main as main


def test_production_blocks_sqlite_database() -> None:
    with pytest.raises(Exception, match="DATABASE_URL must point to Postgres"):
        Settings(
            app_env="production",
            database=DatabaseSettings(url="sqlite:///./data/dev.db"),
            redis=RedisSettings(url="redis://redis:6379/0"),
            security=SecuritySettings(
                secret_key="production-secret",
                cors_origins=["https://sentifargo.example.com"],
                allowed_hosts=["sentifargo.example.com"],
                force_https=True,
            ),
        )


def test_production_blocks_wildcard_cors() -> None:
    with pytest.raises(Exception, match="CORS_ORIGINS must be explicit"):
        Settings(
            app_env="production",
            database=DatabaseSettings(
                url="postgresql+psycopg2://sentifargo:pw@postgres:5432/sentifargo"
            ),
            redis=RedisSettings(url="redis://redis:6379/0"),
            security=SecuritySettings(
                secret_key="production-secret",
                cors_origins=["*"],
                allowed_hosts=["sentifargo.example.com"],
                force_https=True,
            ),
        )


def test_legacy_runtime_is_disabled_by_default() -> None:
    client = TestClient(app)
    response = client.post("/chat", json={"message": "hello", "use_rag": False})

    assert main._legacy_runtime_enabled is False
    assert response.status_code == 404


def test_canonical_api_requires_auth_without_bypass(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_BYPASS", "false")
    client = TestClient(app)

    response = client.post("/api/chat", json={"message": "hello", "use_rag": False})

    assert response.status_code == 401


def test_detailed_health_requires_auth_without_bypass(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_BYPASS", "false")
    client = TestClient(app)

    response = client.get("/health/detailed")

    assert response.status_code == 401
