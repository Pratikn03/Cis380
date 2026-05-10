from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.rag_dsa.ingest import ingest
from app.rag_dsa.pipeline import run_dsa_rag
from app.rag_dsa.config import settings
from app.utils.uploads import MAX_DOC_BYTES, TEXT_EXTENSIONS, read_upload_bytes, validate_upload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dsa-rag")


class AskRequest(BaseModel):
    query: str


class IngestRequest(BaseModel):
    filename: Optional[str] = None
    content: Optional[str] = None


@router.post("/ask")
def ask(req: AskRequest) -> dict[str, Any]:
    try:
        return run_dsa_rag(req.query)
    except Exception as exc:
        logger.exception("RAG pipeline error: %s", exc)
        raise HTTPException(status_code=500, detail="An internal error occurred processing your query.")


@router.post("/ingest")
def ingest_docs(payload: IngestRequest) -> dict[str, Any]:
    docs_dir = Path(settings.DOCS_DIR)
    if payload.filename and payload.content:
        target = docs_dir / Path(payload.filename).name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(payload.content, encoding="utf-8")
    count = ingest()
    return {"status": "ok", "chunks": count}


@router.post("/upload")
async def upload_doc(file: UploadFile = File(...)) -> dict[str, Any]:
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
    docs_dir = Path(settings.DOCS_DIR)
    docs_dir.mkdir(parents=True, exist_ok=True)
    target = docs_dir / filename
    target.write_text(content, encoding="utf-8")
    count = ingest()
    return {"status": "ok", "filename": filename, "chunks": count}
