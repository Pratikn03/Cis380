from fastapi.testclient import TestClient

from app.main import app


def test_recommender_endpoints():
    client = TestClient(app)
    response = client.post("/api/recommend", json={"user_id": "test-user", "top_k": 3})
    assert response.status_code == 200
    payload = response.json()
    assert "items" in payload
    items = payload["items"]
    assert isinstance(items, list)
    assert len(items) > 0

    first_item = items[0]
    explain_resp = client.post(
        "/api/recommend/explain", json={"user_id": "test-user", "item_id": first_item["item_id"]}
    )
    assert explain_resp.status_code == 200
    explain_payload = explain_resp.json()
    assert "explanation" in explain_payload
