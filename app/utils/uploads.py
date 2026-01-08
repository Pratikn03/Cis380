from __future__ import annotations

import os
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp"}

AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac", ".webm"}
AUDIO_MIME_TYPES = {
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/aac",
    "audio/mp4",
    "audio/ogg",
    "audio/flac",
    "audio/webm",
}

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
VIDEO_MIME_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/x-msvideo",
    "video/x-matroska",
    "video/webm",
}

CSV_EXTENSIONS = {".csv"}
TEXT_EXTENSIONS = {".txt", ".md"}


def _max_bytes_from_mb(mb: int) -> int:
    return int(mb) * 1024 * 1024


MAX_IMAGE_BYTES = _max_bytes_from_mb(int(os.getenv("MAX_IMAGE_UPLOAD_MB", "10")))
MAX_AUDIO_BYTES = _max_bytes_from_mb(int(os.getenv("MAX_AUDIO_UPLOAD_MB", "25")))
MAX_VIDEO_BYTES = _max_bytes_from_mb(int(os.getenv("MAX_VIDEO_UPLOAD_MB", "200")))
MAX_DOC_BYTES = _max_bytes_from_mb(int(os.getenv("MAX_DOC_UPLOAD_MB", "10")))
MAX_CSV_BYTES = _max_bytes_from_mb(int(os.getenv("MAX_CSV_UPLOAD_MB", "25")))


def _file_ext(file: UploadFile) -> str:
    if not file.filename:
        return ""
    return Path(file.filename).suffix.lower()


def validate_upload(
    file: UploadFile,
    *,
    allowed_exts: set[str],
    allowed_mimes: set[str] | None = None,
    max_bytes: int,
    kind: str,
) -> None:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing {kind} filename.",
        )
    ext = _file_ext(file)
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported {kind} type: {ext or 'unknown'}.",
        )
    if file.content_type and allowed_mimes and file.content_type not in allowed_mimes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported {kind} MIME type: {file.content_type}.",
        )
    if max_bytes <= 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload size limit is misconfigured.",
        )


async def read_upload_bytes(file: UploadFile, *, max_bytes: int, kind: str) -> bytes:
    data = await file.read()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Uploaded {kind} file was empty.",
        )
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"{kind.capitalize()} exceeds upload limit ({max_bytes} bytes).",
        )
    return data
