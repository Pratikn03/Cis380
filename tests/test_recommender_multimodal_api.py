from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_recommender_multimodal_endpoint_returns_503_when_index_missing(monkeypatch):
    # Avoid loading any heavy deps; we only want to verify API behavior when index isn't built.
    from app.models.recommender.multimodal import multimodal_predict

    def _boom(*args, **kwargs):
        raise multimodal_predict.IndexNotBuiltError("index missing")

    monkeypatch.setattr(multimodal_predict, "multimodal_recommend", _boom)

    client = TestClient(app)
    resp = client.post("/api/recommend/multimodal", data={"text": "gaming laptop", "top_k": "3"})
    assert resp.status_code == 503
    payload = resp.json()
    assert "detail" in payload


def test_recommender_multimodal_endpoint_accepts_text(monkeypatch):
    from app.models.recommender.multimodal import multimodal_predict

    def _ok(*args, **kwargs):
        return {
            "type": "multimodal_recommendation",
            "mode": "text",
            "hits": [{"path": "x.jpg", "score": 0.9}],
            "items": [{"item_id": "x.jpg", "title": "x.jpg", "image_path": "x.jpg", "score": 0.9}],
            "explanation": "ok",
        }

    monkeypatch.setattr(multimodal_predict, "multimodal_recommend", _ok)
    client = TestClient(app)
    resp = client.post("/api/recommend/multimodal", data={"text": "gaming laptop", "top_k": "3"})
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert isinstance(data["items"], list)


def test_recommender_multimodal_endpoint_accepts_text_and_image(monkeypatch):
    from app.models.recommender.multimodal import multimodal_predict

    seen: dict[str, object] = {}

    def _ok(*, image_bytes=None, text=None, top_k=5, paths=None):
        seen["has_image"] = bool(image_bytes)
        seen["text"] = text
        return {
            "type": "multimodal_recommendation",
            "mode": "both",
            "hits": [{"path": "x.jpg", "score": 0.9}],
            "items": [{"item_id": "x.jpg", "title": "x.jpg", "image_path": "x.jpg", "score": 0.9}],
            "explanation": "ok",
        }

    monkeypatch.setattr(multimodal_predict, "multimodal_recommend", _ok)
    client = TestClient(app)
    resp = client.post(
        "/api/recommend/multimodal",
        data={"text": "gaming laptop", "top_k": "3"},
        files={"image": ("x.jpg", b"not-a-real-image", "image/jpeg")},
    )
    assert resp.status_code == 200
    assert seen.get("has_image") is True
    assert seen.get("text") == "gaming laptop"
