from fastapi.testclient import TestClient

from app.main import app


def test_behavior_logs_endpoint_accepts_csv():
    client = TestClient(app)
    csv_bytes = b"user,date,pc,action,ip\nu1,2025-01-01T00:00:00Z,PC-01,login,10.0.0.1\nu1,2025-01-01T00:01:00Z,PC-01,login,10.0.0.1\nu2,2025-01-01T00:00:30Z,PC-02,logout,10.0.0.2\n"
    resp = client.post(
        "/api/behavior/logs",
        files={"file": ("log.csv", csv_bytes, "text/csv")},
        params={"max_rows": 1000, "top_n": 5},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) >= {"filename", "summary", "top_anomalous"}
    assert body["summary"]["users_scored"] >= 1
    assert isinstance(body["top_anomalous"], list)
    assert set(body["top_anomalous"][0].keys()) >= {"lof_score", "anomaly_score", "features"}
    assert 0.0 <= body["top_anomalous"][0]["anomaly_score"] <= 1.0
