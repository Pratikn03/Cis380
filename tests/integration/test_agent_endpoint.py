"""Integration tests for the agent SSE endpoint.

We use FastAPI's TestClient against the in-process app. AUTH_BYPASS is
forced on so we don't need a real JWT. The Anthropic client is monkey-
patched so we don't make network calls.
"""

from __future__ import annotations

import json
import os
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _force_auth_bypass(monkeypatch):
    monkeypatch.setenv("AUTH_BYPASS", "true")
    monkeypatch.setenv("APP_ENV", "development")


@pytest.fixture
def client():
    from app.main import app

    return TestClient(app)


def _parse_sse(body: str) -> list[tuple[str, dict]]:
    """Split an SSE response into (event_name, data_dict) tuples."""
    out = []
    for frame in body.split("\n\n"):
        ev, payload = None, None
        for line in frame.split("\n"):
            if line.startswith("event:"):
                ev = line.replace("event:", "").strip()
            elif line.startswith("data:"):
                try:
                    payload = json.loads(line.replace("data:", "").strip())
                except json.JSONDecodeError:
                    pass
        if ev and payload is not None:
            out.append((ev, payload))
    return out


def test_tools_catalogue(client):
    resp = client.get("/api/v1/agent/tools")
    assert resp.status_code == 200
    body = resp.json()
    names = [t["name"] for t in body["tools"]]
    # Spot-check critical tools
    for required in ("rag_search", "fraud_score", "risk_score", "brand_detect"):
        assert required in names, f"missing tool {required}"
    # Each tool has an input_schema
    assert all("input_schema" in t for t in body["tools"])


def test_run_offline_falls_back(client):
    """With no Anthropic key configured the offline path runs the legacy
    keyword router and returns a final_envelope."""
    resp = client.post(
        "/api/v1/agent/run",
        data={"message": "is this transaction fraudulent: $5000 from RU"},
    )
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types = [e[0] for e in events]
    assert "trace_start" in types
    assert "triage" in types
    assert "final_envelope" in types
    envelope = next(payload for ev, payload in events if ev == "final_envelope")["envelope"]
    assert envelope["intent"] in ("fraud", "risk")
    assert envelope["answer"]
    assert envelope["answer_source"] == "legacy_fallback"


def test_trace_endpoint_404(client):
    resp = client.get("/api/v1/agent/trace/does-not-exist")
    assert resp.status_code == 404


def test_trace_endpoint_returns_entries_for_recent_run(client):
    """Run the agent and then fetch its trace."""
    resp = client.post(
        "/api/v1/agent/run",
        data={"message": "hi"},
    )
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    trace_id = next(p["trace_id"] for ev, p in events if ev == "trace_start")
    trace_resp = client.get(f"/api/v1/agent/trace/{trace_id}")
    assert trace_resp.status_code == 200
    body = trace_resp.json()
    assert body["trace_id"] == trace_id
    assert any(e["event_type"] == "trace_start" for e in body["entries"])
    assert any(e["event_type"] == "trace_end" for e in body["entries"])


def test_pii_scrubbed_in_trace(client):
    """Email + SSN in the input should be redacted before the audit trail
    sees them."""
    resp = client.post(
        "/api/v1/agent/run",
        data={"message": "contact alice@example.com or use 123-45-6789 for verification"},
    )
    events = _parse_sse(resp.text)
    trace_id = next(p["trace_id"] for ev, p in events if ev == "trace_start")
    trace = client.get(f"/api/v1/agent/trace/{trace_id}").json()
    start_entry = next(e for e in trace["entries"] if e["event_type"] == "trace_start")
    text = start_entry.get("text") or ""
    assert "alice@example.com" not in text
    assert "123-45-6789" not in text
    assert "[REDACTED:EMAIL]" in text
    assert "[REDACTED:SSN]" in text


def test_run_with_image_attachment(client, tmp_path):
    """Multipart upload with an image must be accepted (offline path returns
    the legacy fallback envelope, which is fine)."""
    img_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32  # minimal PNG header
    image_path = tmp_path / "test.png"
    image_path.write_bytes(img_bytes)

    with image_path.open("rb") as fh:
        resp = client.post(
            "/api/v1/agent/run",
            data={"message": "what brand is in this logo?"},
            files={"image": ("test.png", fh, "image/png")},
        )
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types = [e[0] for e in events]
    assert "final_envelope" in types
