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
    # Prefer the embeddings/vector-store pipeline if available; fall back to TF-IDF.
    try:
        from app.rag.retriever import retrieve_context

        chunks = retrieve_context(req.query, top_k=req.top_k or 3)
        passages = [
            {
                "text": c.get("text"),
                "score": round(float(c.get("score") or 0.0), 6),
                "source": c.get("source"),
                "chunk_id": c.get("chunk_id"),
            }
            for c in chunks
        ]
        answer = (
            "\n\n".join([str(p.get("text") or "") for p in passages if p.get("text")])
            if passages
            else ""
        )
        citations = [p.get("chunk_id") for p in passages if p.get("chunk_id")]
        return {
            "query": req.query,
            "passages": passages,
            "answer": answer,
            "citations": citations,
            "mode": "vector_store",
        }
    except Exception:
        result = rag_service.query(req.query, top_k=req.top_k or 3)
        return {
            "query": req.query,
            "passages": [
                {
                    "text": p.text,
                    "score": round(float(s), 6),
                    "source": p.source,
                    "chunk_id": p.chunk_id,
                }
                for p, s in result.passages
            ],
            "answer": result.best_text(),
            "citations": [p.chunk_id for p, _ in result.passages],
            "mode": "tfidf",
        }
