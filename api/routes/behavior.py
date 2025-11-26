from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/api/behavior", tags=["behavior"])


class BehaviorRequest(BaseModel):
    features: list[float]


@router.post("")
def predict_behavior(req: BehaviorRequest):
    # Placeholder: load behavior model and score
    return {"score": None, "detail": "Behavior model not wired in this stub."}
