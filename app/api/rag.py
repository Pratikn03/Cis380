from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.rag.ingest import ingest_all_docs

router = APIRouter(prefix="/rag")


class IngestRequest(BaseModel):
    filename: Optional[str] = None
    content: Optional[str] = None


@router.post("/ingest")
async def ingest_docs(payload: IngestRequest) -> Dict[str, Any]:
    if payload.filename and payload.content:
        target = Path("docs") / payload.filename
        target.write_text(payload.content, encoding="utf-8")
    count = ingest_all_docs()
    return {"status": "ok", "chunks": count}
