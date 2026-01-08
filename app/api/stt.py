from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.services.stt.whisper_stt import WhisperSTT
from app.utils.uploads import (
    AUDIO_EXTENSIONS,
    AUDIO_MIME_TYPES,
    MAX_AUDIO_BYTES,
    read_upload_bytes,
    validate_upload,
)

router = APIRouter(prefix="/stt", tags=["stt"])


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = Form(default=None),
) -> Dict[str, Any]:
    validate_upload(
        file,
        allowed_exts=AUDIO_EXTENSIONS,
        allowed_mimes=AUDIO_MIME_TYPES,
        max_bytes=MAX_AUDIO_BYTES,
        kind="audio",
    )
    audio_bytes = await read_upload_bytes(file, max_bytes=MAX_AUDIO_BYTES, kind="audio")

    suffix = ".wav"
    if file.filename and "." in file.filename:
        suffix = "." + file.filename.split(".")[-1].lower()

    try:
        payload = WhisperSTT.transcribe_bytes(audio_bytes, suffix=suffix, language=language)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"STT failed: {exc}")

    payload["filename"] = file.filename
    return payload
