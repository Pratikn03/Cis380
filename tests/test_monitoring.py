from fastapi.testclient import TestClient

from app.main import app


def test_monitor_workflow(tmp_path):
    client = TestClient(app)
    log_event = {
        "timestamp": "2025-12-12T00:00:00Z",
        "request_id": "test-1",
        "user_id": "tester",
        "model_version": "fraud_v1",
        "features_summary": {"amount": 120.0, "hour": 10},
        "prediction_score": 0.2,
        "prediction_label": "low",
        "latency_ms": 20.0,
    }
    resp = client.post("/api/monitor/log", json=log_event)
    assert resp.status_code == 200
    summary = client.get("/api/monitor/summary?window_n=10").json()
    assert "count" in summary
    base_resp = client.post("/api/monitor/baseline/build", json={"events_n": 10})
    assert base_resp.status_code == 200
    drift = client.get("/api/monitor/drift?window_n=10").json()
    assert "drift_score" in drift and "status" in drift
