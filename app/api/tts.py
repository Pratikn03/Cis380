from __future__ import annotations

import os
import subprocess
import tempfile

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from pydantic import BaseModel

router = APIRouter(prefix="/tts", tags=["tts"])


class TTSPayload(BaseModel):
    text: str


def _cleanup(path: str) -> None:
    try:
        os.remove(path)
    except OSError:
        pass


@router.post("/speak")
def tts_speak(payload: TTSPayload):
    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is required.")

    piper_bin = os.getenv("PIPER_BIN")
    piper_model = os.getenv("PIPER_MODEL")
    piper_config = os.getenv("PIPER_CONFIG", "")

    if not piper_bin or not piper_model:
        raise HTTPException(
            status_code=503,
            detail="Configure PIPER_BIN and PIPER_MODEL environment variables to enable TTS.",
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        out_path = tmp.name

    cmd = [piper_bin, "--model", piper_model, "--output_file", out_path]
    if piper_config:
        cmd += ["--config", piper_config]

    proc = subprocess.run(
        cmd,
        input=text.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    if proc.returncode != 0:
        _cleanup(out_path)
        raise HTTPException(
            status_code=500,
            detail=f"Piper failed: {proc.stderr.decode('utf-8', errors='ignore')[:400]}",
        )

    return FileResponse(
        out_path,
        media_type="audio/wav",
        filename="tts.wav",
        background=BackgroundTask(_cleanup, out_path),
    )
