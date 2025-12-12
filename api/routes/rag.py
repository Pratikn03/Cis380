from fastapi import APIRouter, Depends
from pydantic import BaseModel

from rag.service import rag_service
from api.deps import require_auth

router = APIRouter(prefix="/api/rag", tags=["rag"], dependencies=[Depends(require_auth)])


class RAGQuery(BaseModel):
    query: str
    top_k: int | None = 3


@router.post("/query")
def rag_query(req: RAGQuery):
    """Return top passages from local docs (data/docs)."""
    result = rag_service.query(req.query, top_k=req.top_k or 3)
    return {
        "query": req.query,
        "passages": [{"text": p, "score": s} for p, s in result.passages],
        "answer": result.best_text(),
    }
