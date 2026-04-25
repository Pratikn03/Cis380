from __future__ import annotations

import os

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.utils.uploads import (
    AUDIO_EXTENSIONS,
    AUDIO_MIME_TYPES,
    MAX_AUDIO_BYTES,
    validate_upload,
)

router = APIRouter(prefix="/voice")


@router.post("/emotion")
def voice_emotion(file: UploadFile = File(...)) -> dict[str, object]:
    # Changed from async def to def to run in threadpool (CPU-bound task)
    validate_upload(
        file,
        allowed_exts=AUDIO_EXTENSIONS,
        allowed_mimes=AUDIO_MIME_TYPES,
        max_bytes=MAX_AUDIO_BYTES,
        kind="audio",
    )
    # Note: We cannot await inside a sync def.
    # Ideally, read bytes async, then offload processing.
    # For simplicity in FastAPI, keeping it sync reads file in threadpool.
    audio_bytes = file.file.read(MAX_AUDIO_BYTES + 1)
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Uploaded audio file was empty.")
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Audio exceeds upload limit ({MAX_AUDIO_BYTES} bytes).",
        )

    backend = os.getenv("VOICE_EMOTION_BACKEND", "mfcc").lower()
    try:
        if backend in {"ssl", "wav2vec2", "hubert", "wavlm"}:
            from app.models.voice.emotion_ssl_predict import predict_emotion_ssl, ssl_available

            if ssl_available():
                payload = predict_emotion_ssl(audio_bytes=audio_bytes, filename=file.filename)
            else:
                from app.models.voice.emotion_predict import predict_emotion

                payload = predict_emotion(audio_bytes=audio_bytes, filename=file.filename)
        else:
            from app.models.voice.emotion_predict import predict_emotion

            payload = predict_emotion(audio_bytes=audio_bytes, filename=file.filename)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    payload["filename"] = file.filename
    return payload
