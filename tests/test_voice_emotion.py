from fastapi.testclient import TestClient
import numpy as np
import wave

from app.main import app


def test_voice_emotion_endpoint(tmp_path):
    client = TestClient(app)
    sr = 22050
    t = np.linspace(0, 0.5, int(0.5 * sr), False)
    signal = 0.5 * np.sin(2 * np.pi * 220 * t)
    path = tmp_path / "sample.wav"
    with wave.open(path, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(sr)
        audio_bytes = (signal * 32767).astype(np.int16).tobytes()
        writer.writeframes(audio_bytes)
    with path.open("rb") as handle:
        files = {"file": ("sample.wav", handle.read(), "audio/wav")}
        resp = client.post("/api/voice/emotion", files=files)
    assert resp.status_code == 200
    payload = resp.json()
    assert "emotion" in payload
    assert "confidence" in payload
