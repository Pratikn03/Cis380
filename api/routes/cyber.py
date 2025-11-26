from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/cyber", tags=["cyber"])


class CyberRequest(BaseModel):
    features: list[float]


@router.post("")
def predict_cyber(req: CyberRequest):
    # Placeholder: integrate existing cyber model from models/cyber/supervised
    return {"score": None, "detail": "Cyber model not wired in this stub."}
