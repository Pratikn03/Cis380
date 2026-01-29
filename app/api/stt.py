from __future__ import annotations

from typing import Any, Dict, Optional

import base64
import json
import os

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool

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
    language = (language or os.getenv("STT_LANGUAGE") or "en").strip() or None
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


@router.websocket("/stream")
async def stream_transcription(websocket: WebSocket) -> None:
    """
    Real-time (chunked) STT over WebSocket.

    Client protocol (JSON text messages):
      - {"type": "config", "language": "en", "suffix": ".wav", "partial": true, "min_bytes": 48000}
      - {"type": "chunk", "audio": "<base64-bytes>", "final": false}
      - {"type": "final"}  # triggers final transcription of buffered audio

    Binary WebSocket frames are treated as raw audio chunks.
    """
    await websocket.accept()
    buffer = bytearray()
    language = (os.getenv("STT_LANGUAGE") or "en").strip() or None
    suffix = ".wav"
    partial = False
    min_bytes = int(os.getenv("STT_STREAM_MIN_BYTES", "48000"))
    last_partial_size = 0

    try:
        while True:
            message = await websocket.receive()
            if "bytes" in message and message["bytes"] is not None:
                buffer.extend(message["bytes"])
                if len(buffer) > MAX_AUDIO_BYTES:
                    await websocket.send_json(
                        {"error": f"Audio exceeds upload limit ({MAX_AUDIO_BYTES} bytes)."}
                    )
                    break
                if partial and len(buffer) >= last_partial_size + min_bytes:
                    payload = await run_in_threadpool(
                        WhisperSTT.transcribe_bytes, bytes(buffer), suffix=suffix, language=language
                    )
                    payload["final"] = False
                    await websocket.send_json(payload)
                    last_partial_size = len(buffer)
                continue

            text = message.get("text")
            if not text:
                continue
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON payload."})
                continue

            msg_type = data.get("type", "chunk")
            if msg_type == "config":
                language = (data.get("language") or language or "en").strip() or None
                suffix = data.get("suffix") or suffix
                if suffix and not suffix.startswith("."):
                    suffix = f".{suffix}"
                partial = bool(data.get("partial", partial))
                min_bytes = int(data.get("min_bytes", min_bytes))
                await websocket.send_json(
                    {
                        "type": "config_ack",
                        "language": language,
                        "suffix": suffix,
                        "partial": partial,
                        "min_bytes": min_bytes,
                    }
                )
                continue

            if msg_type == "final":
                if not buffer:
                    await websocket.send_json({"error": "No audio buffered for transcription."})
                    continue
                payload = await run_in_threadpool(
                    WhisperSTT.transcribe_bytes, bytes(buffer), suffix=suffix, language=language
                )
                payload["final"] = True
                await websocket.send_json(payload)
                buffer.clear()
                last_partial_size = 0
                continue

            audio_b64 = data.get("audio")
            if audio_b64:
                try:
                    chunk = base64.b64decode(audio_b64)
                except (TypeError, ValueError):
                    await websocket.send_json({"error": "Invalid base64 audio chunk."})
                    continue
                buffer.extend(chunk)

            if len(buffer) > MAX_AUDIO_BYTES:
                await websocket.send_json(
                    {"error": f"Audio exceeds upload limit ({MAX_AUDIO_BYTES} bytes)."}
                )
                break

            if data.get("final"):
                if not buffer:
                    await websocket.send_json({"error": "No audio buffered for transcription."})
                    continue
                payload = await run_in_threadpool(
                    WhisperSTT.transcribe_bytes, bytes(buffer), suffix=suffix, language=language
                )
                payload["final"] = True
                await websocket.send_json(payload)
                buffer.clear()
                last_partial_size = 0
                continue

            if partial and len(buffer) >= last_partial_size + min_bytes:
                payload = await run_in_threadpool(
                    WhisperSTT.transcribe_bytes, bytes(buffer), suffix=suffix, language=language
                )
                payload["final"] = False
                await websocket.send_json(payload)
                last_partial_size = len(buffer)
    except WebSocketDisconnect:
        return
