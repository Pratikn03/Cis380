from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/rag", tags=["rag"])


class RAGQuery(BaseModel):
    query: str


@router.post("/query")
def rag_query(req: RAGQuery):
    # Placeholder: call retriever and LLM with context
    return {"answer": "RAG not wired yet", "query": req.query}
