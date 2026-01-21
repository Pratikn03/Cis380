import os

import pytest
import requests

BASE = os.getenv("BASE_URL", "http://localhost:8000")


def _server_up() -> bool:
    try:
        response = requests.get(BASE + "/api/health", timeout=3)
        return response.status_code == 200
    except Exception:
        return False


def test_health():
    if not _server_up():
        pytest.skip("API not running for e2e tests")
    response = requests.get(BASE + "/api/health", timeout=10)
    assert response.status_code == 200


def test_chat():
    if not _server_up():
        pytest.skip("API not running for e2e tests")
    response = requests.post(BASE + "/api/chat", json={"text": "hello", "mode": "auto"}, timeout=30)
    assert response.status_code in (200, 422)
