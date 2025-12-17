from fastapi.testclient import TestClient
import io
import numpy as np
import wave

from app.main import app


def _make_wav_bytes(*, seconds: float = 0.5, sr: int = 22050) -> bytes:
    t = np.linspace(0, seconds, int(seconds * sr), False)
    signal = 0.5 * np.sin(2 * np.pi * 220 * t)
    audio_bytes = (signal * 32767).astype(np.int16).tobytes()
    buf = io.BytesIO()
    with wave.open(buf, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(sr)
        writer.writeframes(audio_bytes)
    return buf.getvalue()


def test_chat_multimodal_transcribe_flag_does_not_break():
    client = TestClient(app)
    wav_bytes = _make_wav_bytes()

    resp = client.post(
        "/api/chat/multimodal",
        data={
            "message": "hello",
            "instruction": "",
            "user_id": "tester",
            "use_rag": "false",
            "transcribe_audio": "true",
        },
        files={"audio": ("sample.wav", wav_bytes, "audio/wav")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert {"route", "answer", "meta"} <= body.keys()
    assert isinstance(body.get("meta"), dict)
    attachments = (body.get("meta") or {}).get("attachments") or {}
    # Voice should always attach; STT may be either a result or an error (depending on env).
    assert "voice" in attachments or "voice_error" in attachments
    assert ("stt" in attachments) or ("stt_error" in attachments)
