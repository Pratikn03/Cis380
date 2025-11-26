from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/api/fraud", tags=["fraud"])


class FraudRequest(BaseModel):
    features: list[float]


@router.post("")
def predict_fraud(req: FraudRequest):
    # Placeholder: integrate existing fraud model from models/fraud/supervised
    return {"score": None, "detail": "Fraud model not wired in this stub."}
