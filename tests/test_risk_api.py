from fastapi.testclient import TestClient

from app.main import app


def test_risk_analyze_endpoint_happy_path():
    client = TestClient(app)
    payload = {
        "login_country": "US",
        "device_known": True,
        "login_time": 12,
        "clicks_per_minute": 5,
        "files_accessed": 0,
        "transaction_amount": 0.0,
    }
    resp = client.post("/api/risk/analyze", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) >= {"cyber_risk", "behavior_risk", "fraud_risk", "fusion_risk", "decision", "reason_code"}
    assert 0.0 <= body["cyber_risk"] <= 1.0
    assert 0.0 <= body["behavior_risk"] <= 1.0
    assert 0.0 <= body["fraud_risk"] <= 1.0
    assert 0.0 <= body["fusion_risk"] <= 1.0
    assert body["decision"] in {"ALLOW", "STEP_UP_AUTH", "BLOCK"}
