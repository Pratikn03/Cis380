from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.models.voice.emotion_predict import predict_emotion
from app.utils.uploads import (
    AUDIO_EXTENSIONS,
    AUDIO_MIME_TYPES,
    MAX_AUDIO_BYTES,
    read_upload_bytes,
    validate_upload,
)

router = APIRouter(prefix="/voice")


@router.post("/emotion")
async def voice_emotion(file: UploadFile = File(...)) -> dict[str, object]:
    validate_upload(
        file,
        allowed_exts=AUDIO_EXTENSIONS,
        allowed_mimes=AUDIO_MIME_TYPES,
        max_bytes=MAX_AUDIO_BYTES,
        kind="audio",
    )
    audio_bytes = await read_upload_bytes(file, max_bytes=MAX_AUDIO_BYTES, kind="audio")
    try:
        payload = predict_emotion(audio_bytes=audio_bytes, filename=file.filename)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    payload["filename"] = file.filename
    return payload
