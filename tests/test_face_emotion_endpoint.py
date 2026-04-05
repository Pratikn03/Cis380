from fastapi.testclient import TestClient

from app.main import app


def test_face_emotion_predict_no_file():
    client = TestClient(app)
    resp = client.post("/api/vision/face_emotion/predict")
    assert resp.status_code in [400, 422]


def test_face_emotion_predict_invalid_file():
    client = TestClient(app)
    resp = client.post(
        "/api/vision/face_emotion/predict",
        files={"file": ("test.txt", b"invalid content", "text/plain")},
    )
    # Depending on whether the model is trained locally, this can fail before/after model load.
    assert resp.status_code in [400, 422, 500, 503]
