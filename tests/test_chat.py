from fastapi.testclient import TestClient

from app.main import app


def test_chat_route():
    client = TestClient(app)
    response = client.post("/api/chat", json={"text": "Recommend a movie", "user_id": "tester"})
    assert response.status_code == 200
    payload = response.json()
    assert {"route", "answer", "meta"} <= payload.keys()
    assert isinstance(payload["route"], str)
    assert isinstance(payload["answer"], str)
