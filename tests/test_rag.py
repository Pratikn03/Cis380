from fastapi.testclient import TestClient

from app.main import app


def test_rag_ingest_and_chat():
    client = TestClient(app)
    ingest_resp = client.post(
        "/api/rag/ingest",
        json={
            "filename": "test_rag_upload.txt",
            "content": "Sentifargo local-first RAG ensures answers mention local-first RAG.",
        },
    )
    assert ingest_resp.status_code == 200
    chat_resp = client.post(
        "/api/chat",
        json={"text": "According to the document, what is Sentifargo?", "user_id": "rag-user"},
    )
    assert chat_resp.status_code == 200
    payload = chat_resp.json()
    assert payload["route"] == "rag"
    meta = payload["meta"]
    assert isinstance(meta.get("citations"), list)
    assert meta["citations"], "Expected citations from RAG retrieval"
