from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.models import Job, RagQueryLog
from app.db.session import get_db
from app.rag.dsa_pipeline import answer_query, ingest_documents
from app.rag.config import settings as rag_settings
from app.services.audit import record_audit
from app.workers import tasks
from app.utils.uploads import DOC_EXTENSIONS, MAX_DOC_BYTES, read_upload_bytes, validate_upload

router = APIRouter(prefix="/rag", tags=["rag"], dependencies=[Depends(get_current_user)])


class RagQueryRequest(BaseModel):
    query: str
    top_k: int = 6
    return_chunks: bool = True


@router.post("/upload")
async def upload_docs(
    file: UploadFile = File(...), db: Session = Depends(get_db)
) -> dict[str, Any]:
    validate_upload(
        file,
        allowed_exts=DOC_EXTENSIONS,
        allowed_mimes=None,
        max_bytes=MAX_DOC_BYTES,
        kind="document",
    )
    filename = (file.filename or "upload.txt").split("/")[-1]
    raw = await read_upload_bytes(file, max_bytes=MAX_DOC_BYTES, kind="document")
    target = rag_settings.docs_dir / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    stats = ingest_documents()
    record_audit(db, action="upload_doc", target=filename)
    return {"status": "ok", "filename": filename, **stats}


@router.post("/index")
def build_index(rebuild: bool = False, db: Session = Depends(get_db)) -> dict[str, Any]:
    job = Job(
        job_type="rag_index",
        status="queued",
        progress=0.0,
        message="queued",
        payload={"rebuild": rebuild},
        created_at=datetime.utcnow(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    result = tasks.rag_index.delay(job.id, rebuild=rebuild)
    job.task_id = result.id
    db.commit()
    record_audit(db, action="rag_index", target=job.id)
    return {"status": "queued", "job_id": job.id, "task_id": job.task_id}


@router.post("/eval")
def evaluate_rag(db: Session = Depends(get_db)) -> dict[str, Any]:
    job = Job(
        job_type="rag_eval",
        status="queued",
        progress=0.0,
        message="queued",
        payload={},
        created_at=datetime.utcnow(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    result = tasks.rag_eval.delay(job.id)
    job.task_id = result.id
    db.commit()
    record_audit(db, action="rag_eval", target=job.id)
    return {"status": "queued", "job_id": job.id, "task_id": job.task_id}


@router.post("/query")
def query_rag(payload: RagQueryRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="query is required")
    start = time.perf_counter()
    result = answer_query(payload.query, top_k=payload.top_k)
    latency_ms = (time.perf_counter() - start) * 1000

    sources = result.get("sources") or []
    scores = [item.get("hybrid_score") for item in sources if item.get("hybrid_score") is not None]
    top_score = max(scores) if scores else 0.0
    avg_score = sum(scores) / len(scores) if scores else 0.0
    status = result.get("status", "ok")

    db.add(
        RagQueryLog(
            query=payload.query,
            status=status,
            top_score=top_score,
            avg_score=avg_score,
            latency_ms=latency_ms,
            meta={"top_k": payload.top_k},
        )
    )
    db.commit()

    if not payload.return_chunks:
        result.pop("sources", None)
    return result
