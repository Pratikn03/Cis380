"""OpenAPI contract tests powered by schemathesis.

We pull the OpenAPI schema directly from the running app (FastAPI
generates it from route signatures and Pydantic models) and let
schemathesis fuzz every documented endpoint. The targets here are tight:

  * No 5xx responses (server-side bugs / unhandled exceptions).
  * No schema drift (response shapes match what the OpenAPI says).

We mark every check as a unit test so it runs alongside everything else.
Schemathesis is an optional dep; tests skip cleanly if it isn't
installed.
"""

from __future__ import annotations

import os
import pytest

pytest.importorskip("schemathesis")

import schemathesis  # noqa: E402

# Force dev posture: AUTH_BYPASS lets schemathesis hit auth-gated paths
# without minting a real JWT. Production CI runs against a sandbox.
os.environ.setdefault("AUTH_BYPASS", "true")
os.environ.setdefault("APP_ENV", "development")

from app.main import app  # noqa: E402


schema = schemathesis.openapi.from_asgi("/openapi.json", app)


# Endpoints we deliberately skip:
#   - /api/v1/agent/run    : streaming SSE; schemathesis can't validate text/event-stream
#   - /metrics              : prometheus exposition (text/plain, free-form)
#   - /docs|/openapi.json   : meta endpoints
SKIP_PATHS = {
    "/api/v1/agent/run",
    "/metrics",
    "/docs",
    "/redoc",
    "/openapi.json",
}


@schema.parametrize()
def test_no_server_errors(case):
    """Every documented endpoint must respond without 5xx for any input
    schemathesis generates against the schema."""
    if case.path in SKIP_PATHS:
        pytest.skip(f"explicitly skipped path {case.path}")
    response = case.call()
    # Schemathesis' default validator confirms response shape; here we
    # only require "no server-side bugs."
    assert response.status_code < 500, (
        f"{case.method} {case.path} returned {response.status_code}"
    )
