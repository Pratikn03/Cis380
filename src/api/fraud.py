from fastapi import APIRouter
router = APIRouter(prefix="/api/fraud", tags=["fraud"])

@router.post("/score")
def score(payload: dict):
    # TODO: call FraudService
    return {"route": "fraud", "answer": "stub", "metadata": {"input": payload}, "error": None}
