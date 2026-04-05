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


def test_dsa_doc_rag_roundtrip():
    if not _server_up():
        pytest.skip("API not running for e2e tests")
    ingest = requests.post(
        BASE + "/api/rag/ingest",
        json={
            "filename": "e2e_doc.txt",
            "content": "Sentifargo DSA answers questions using your documents with citations.",
        },
        timeout=30,
    )
    assert ingest.status_code == 200

    ask = requests.post(
        BASE + "/api/rag/ask",
        json={"query": "How does Sentifargo DSA answer questions?"},
        timeout=30,
    )
    assert ask.status_code == 200
    payload = ask.json()
    assert payload.get("answer")
    citations = payload.get("citations") or []
    assert citations, "Expected citations from DSA response"
