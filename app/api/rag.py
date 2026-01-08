from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.rag.ingest import ingest_all_docs
from app.utils.uploads import MAX_DOC_BYTES, TEXT_EXTENSIONS, read_upload_bytes, validate_upload

router = APIRouter(prefix="/rag")


class IngestRequest(BaseModel):
    filename: Optional[str] = None
    content: Optional[str] = None


@router.post("/ingest")
async def ingest_docs(payload: IngestRequest) -> Dict[str, Any]:
    if payload.filename and payload.content:
        target = Path("data") / "docs" / payload.filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(payload.content, encoding="utf-8")
    count = ingest_all_docs()
    return {"status": "ok", "chunks": count}


@router.post("/upload")
async def upload_doc(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Upload a .txt/.md doc into `data/docs/` and rebuild the local RAG index."""
    validate_upload(
        file,
        allowed_exts=TEXT_EXTENSIONS,
        allowed_mimes=None,
        max_bytes=MAX_DOC_BYTES,
        kind="document",
    )
    filename = Path(file.filename or "upload.md").name
    raw = await read_upload_bytes(file, max_bytes=MAX_DOC_BYTES, kind="document")
    content = raw.decode("utf-8", errors="ignore")
    target = Path("data") / "docs" / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    count = ingest_all_docs()
    return {"status": "ok", "filename": filename, "chunks": count}
