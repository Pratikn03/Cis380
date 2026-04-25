import base64

from app.api import agent, behavior, cyber_timeline, fraud
from app.api.v1 import auth as auth_api
from app.api.v1 import admin_dashboard, user_settings


def test_phase5_routes_are_registered() -> None:
    routers = [
        ("/api", agent.router),
        ("/api", fraud.router),
        ("/api", behavior.router),
        ("", cyber_timeline.router),
        ("/api/v1", admin_dashboard.router),
        ("/api/v1", user_settings.router),
        ("/api/v1", auth_api.router),
    ]
    registered = {prefix + route.path for prefix, router in routers for route in router.routes}

    assert {
        "/api/agent/stream",
        "/api/agent/escalate",
        "/api/fraud/explain",
        "/api/behavior/logs",
        "/api/cyber/timeline",
        "/api/cyber/timeline/events",
        "/api/cyber/timeline/summary",
        "/api/v1/admin/model-registry",
        "/api/v1/admin/feature-flags",
        "/api/v1/admin/audit-logs",
        "/api/v1/users/me/settings",
        "/api/v1/auth/logout",
        "/api/v1/auth/password-reset/request",
        "/api/v1/auth/password-reset/confirm",
        "/api/v1/auth/totp/enroll",
        "/api/v1/auth/totp/verify",
    }.issubset(registered)


def test_totp_helper_accepts_current_and_neighbor_windows() -> None:
    secret = base64.b32encode(b"sentifargo-phase5-secret").decode("ascii")
    code = auth_api._totp_code(secret, step=1_900_000)

    original_time = auth_api.time.time
    try:
        auth_api.time.time = lambda: 1_900_000 * 30
        assert auth_api._verify_totp(secret, code)
        assert not auth_api._verify_totp(secret, "00000")
    finally:
        auth_api.time.time = original_time


def test_password_reset_token_fallback_is_single_use(monkeypatch) -> None:
    monkeypatch.delenv("REDIS_URL", raising=False)
    auth_api._RESET_TOKENS.clear()

    auth_api._store_reset_token("user-123", "reset-token", ttl_seconds=60)

    assert auth_api._consume_reset_token("reset-token") == "user-123"
    assert auth_api._consume_reset_token("reset-token") is None
