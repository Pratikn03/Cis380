from __future__ import annotations

import base64
import binascii
import ipaddress
import os
from pathlib import Path
from urllib.parse import urlparse

import requests
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
DOC_EXTENSIONS = {".txt", ".md", ".pdf", ".docx", ".html", ".htm", ".json", ".csv"}


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


def _bool_env(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _allowed_media_hosts() -> set[str]:
    raw = os.getenv("ALLOWED_MEDIA_HOSTS", "").strip()
    if not raw:
        return set()
    return {host.strip().lower() for host in raw.split(",") if host.strip()}


def _validate_remote_url(url: str) -> tuple[str, str]:
    if not _bool_env("ALLOW_REMOTE_MEDIA", "false"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Remote media loading is disabled. Set ALLOW_REMOTE_MEDIA=true to enable.",
        )
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only http/https URLs are supported.",
        )
    host = (parsed.hostname or "").strip().lower()
    if not host:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL host.",
        )
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Private or local network URLs are not allowed.",
            )
    except ValueError:
        pass
    allowlist = _allowed_media_hosts()
    if allowlist and not any(host == allowed or host.endswith(f".{allowed}") for allowed in allowlist):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Remote host not in ALLOWED_MEDIA_HOSTS.",
        )
    return host, parsed.path or ""


def _decode_base64_data(value: str, *, allowed_mimes: set[str] | None) -> bytes:
    raw = value.strip()
    mime = None
    if raw.startswith("data:"):
        try:
            header, b64 = raw.split(",", 1)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid data URL.",
            ) from exc
        parts = header.split(";")
        if parts:
            mime = parts[0].replace("data:", "").strip().lower()
        raw = b64
    if mime and allowed_mimes and mime not in allowed_mimes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported {mime} content type.",
        )
    try:
        return base64.b64decode(raw, validate=True)
    except binascii.Error as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid base64 payload.",
        ) from exc


def _fetch_remote_bytes(
    url: str,
    *,
    max_bytes: int,
    allowed_mimes: set[str] | None,
    kind: str,
) -> bytes:
    _validate_remote_url(url)
    timeout = float(os.getenv("REMOTE_MEDIA_TIMEOUT_SEC", "15"))
    try:
        resp = requests.get(url, stream=True, timeout=timeout)
        resp.raise_for_status()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not download {kind} URL: {exc}",
        ) from exc

    content_type = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
    if allowed_mimes and content_type and content_type not in allowed_mimes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported {kind} MIME type: {content_type}.",
        )

    content_length = resp.headers.get("Content-Length")
    if content_length and int(content_length) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"{kind.capitalize()} exceeds upload limit ({max_bytes} bytes).",
        )

    data = bytearray()
    for chunk in resp.iter_content(chunk_size=8192):
        if not chunk:
            continue
        data.extend(chunk)
        if len(data) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"{kind.capitalize()} exceeds upload limit ({max_bytes} bytes).",
            )
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{kind.capitalize()} URL returned empty payload.",
        )
    return bytes(data)


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


async def read_image_payload(
    *,
    file: UploadFile | None,
    image_url: str | None,
    image_base64: str | None,
    allowed_exts: set[str],
    allowed_mimes: set[str],
    max_bytes: int,
    kind: str,
) -> bytes:
    if file is not None:
        validate_upload(
            file,
            allowed_exts=allowed_exts,
            allowed_mimes=allowed_mimes,
            max_bytes=max_bytes,
            kind=kind,
        )
        return await read_upload_bytes(file, max_bytes=max_bytes, kind=kind)
    if image_base64:
        data = _decode_base64_data(image_base64, allowed_mimes=allowed_mimes)
        if not data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{kind.capitalize()} base64 payload was empty.",
            )
        if len(data) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"{kind.capitalize()} exceeds upload limit ({max_bytes} bytes).",
            )
        return data
    if image_url:
        return _fetch_remote_bytes(
            image_url,
            max_bytes=max_bytes,
            allowed_mimes=allowed_mimes,
            kind=kind,
        )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Provide a {kind} file, image_url, or image_base64.",
    )
