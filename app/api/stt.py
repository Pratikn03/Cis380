from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.services.stt.whisper_stt import WhisperSTT

router = APIRouter(prefix="/stt", tags=["stt"])


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = Form(default=None),
) -> Dict[str, Any]:
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Uploaded audio file was empty.")

    suffix = ".wav"
    if file.filename and "." in file.filename:
        suffix = "." + file.filename.split(".")[-1].lower()

    try:
        payload = WhisperSTT.transcribe_bytes(audio_bytes, suffix=suffix, language=language)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"STT failed: {exc}")

    payload["filename"] = file.filename
    return payload
