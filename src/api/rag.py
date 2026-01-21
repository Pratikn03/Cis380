from fastapi import APIRouter
router = APIRouter(prefix="/api/rag", tags=["rag"])

@router.post("/query")
def query(payload: dict):
    # TODO: call RAGService
    return {"route": "rag", "answer": "stub", "metadata": {"input": payload}, "error": None}
