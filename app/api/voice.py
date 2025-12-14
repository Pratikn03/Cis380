from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.models.voice.emotion_predict import predict_emotion

router = APIRouter(prefix="/voice")


@router.post("/emotion")
async def voice_emotion(file: UploadFile = File(...)) -> dict[str, object]:
    audio_bytes = await file.read()
    try:
        payload = predict_emotion(audio_bytes=audio_bytes, filename=file.filename)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    payload["filename"] = file.filename
    return payload
