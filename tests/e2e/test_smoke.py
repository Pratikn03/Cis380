import os

import requests

BASE = os.getenv("BASE_URL", "http://localhost:8000")


def test_health():
    response = requests.get(BASE + "/api/health", timeout=10)
    assert response.status_code == 200


def test_chat():
    response = requests.post(BASE + "/api/chat", json={"text": "hello", "mode": "auto"}, timeout=30)
    assert response.status_code in (200, 422)
