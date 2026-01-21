from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.rag.dsa_pipeline import answer_query, delete_document, ingest_documents
from app.rag.config import settings
from app.utils.uploads import (
    DOC_EXTENSIONS,
    MAX_DOC_BYTES,
    read_upload_bytes,
    validate_upload,
)

router = APIRouter(prefix="/rag")


class IngestRequest(BaseModel):
    filename: Optional[str] = None
    content: Optional[str] = None


class AskRequest(BaseModel):
    query: str
    top_k: Optional[int] = None


class QueryRequest(BaseModel):
    query: str
    top_k: int = 6
    return_chunks: bool = True


@router.post("/ingest")
async def ingest_docs(payload: IngestRequest) -> Dict[str, Any]:
    if payload.filename and payload.content:
        target = settings.docs_dir / payload.filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(payload.content, encoding="utf-8")
    stats = ingest_documents()
    return {"status": "ok", **stats}


@router.post("/index")
async def build_index(rebuild: bool = False) -> Dict[str, Any]:
    stats = ingest_documents(rebuild=rebuild)
    return {"status": "ok", **stats}


@router.post("/upload")
async def upload_doc(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Upload a doc into the DSA store and rebuild the local RAG index."""
    validate_upload(
        file,
        allowed_exts=DOC_EXTENSIONS,
        allowed_mimes=None,
        max_bytes=MAX_DOC_BYTES,
        kind="document",
    )
    filename = Path(file.filename or "upload.txt").name
    raw = await read_upload_bytes(file, max_bytes=MAX_DOC_BYTES, kind="document")
    target = settings.docs_dir / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    stats = ingest_documents()
    return {"status": "ok", "filename": filename, **stats}


@router.post("/ask")
async def ask_docs(payload: AskRequest) -> Dict[str, Any]:
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="query is required")
    return answer_query(payload.query, top_k=payload.top_k)


@router.post("/query")
async def query_docs(payload: QueryRequest) -> Dict[str, Any]:
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="query is required")
    result = answer_query(payload.query, top_k=payload.top_k)
    if not payload.return_chunks:
        result.pop("sources", None)
    return result


@router.get("/status")
async def rag_status() -> Dict[str, Any]:
    meta = {}
    if settings.index_meta_path.exists():
        try:
            meta = json.loads(settings.index_meta_path.read_text(encoding="utf-8"))
        except Exception:
            meta = {}
    doc_count = 0
    chunk_count = 0
    if settings.documents_path.exists():
        doc_count = sum(
            1
            for line in settings.documents_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    if settings.chunks_path.exists():
        chunk_count = sum(
            1 for line in settings.chunks_path.read_text(encoding="utf-8").splitlines() if line.strip()
        )
    return {
        "docs_dir": str(settings.docs_dir),
        "output_dir": str(settings.output_dir),
        "index_meta": meta,
        "doc_count": doc_count,
        "chunk_count": chunk_count,
        "embed_model": settings.embed_model,
    }


@router.delete("/docs/{doc_id}")
async def delete_doc(doc_id: str) -> Dict[str, Any]:
    return delete_document(doc_id)
