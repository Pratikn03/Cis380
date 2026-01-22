from fastapi import APIRouter

router = APIRouter(prefix="/api/reco", tags=["reco"])


@router.post("/recommend")
def recommend(payload: dict):
    # TODO: call RecoService
    return {"route": "reco", "answer": "stub", "metadata": {"input": payload}, "error": None}
