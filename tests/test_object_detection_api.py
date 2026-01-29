from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_object_detection_endpoint_handles_missing_weights() -> None:
    client = TestClient(app)
    # 1x1 PNG base64
    payload = {
        "image_base64": (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMA"
            "ASsJTYQAAAAASUVORK5CYII="
        )
    }
    resp = client.post("/api/vision/object/detect", data=payload)
    if resp.status_code == 503:
        detail = resp.json().get("detail", "")
        assert "YOLOv3" in detail or "opencv-python" in detail
        return
    assert resp.status_code == 200
    body = resp.json()
    assert "detections" in body


def test_object_visualize_endpoint_handles_missing_weights() -> None:
    client = TestClient(app)
    payload = {
        "image_base64": (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMA"
            "ASsJTYQAAAAASUVORK5CYII="
        )
    }
    resp = client.post("/api/vision/object/visualize", data=payload)
    if resp.status_code == 503:
        detail = resp.json().get("detail", "")
        assert "YOLOv3" in detail or "opencv-python" in detail
        return
    assert resp.status_code == 200
    assert resp.headers.get("content-type", "").startswith("image/png")
