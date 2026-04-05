from fastapi.testclient import TestClient

from app.main import app


def test_api_health_contract():
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()

    assert body.get("status") == "ok"
    assert body.get("service") == "Sentifargo"
    assert "version" in body
    assert "optional_features" in body
    assert isinstance(body["optional_features"], dict)

    # Ensure keys exist (values may be True/False depending on env)
    assert {"webrtc", "stt", "clip", "faiss"} <= set(body["optional_features"].keys())
