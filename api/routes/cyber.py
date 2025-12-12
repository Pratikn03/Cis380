from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from pathlib import Path
import numpy as np
import joblib

from api.deps import require_auth

router = APIRouter(prefix="/api/cyber", tags=["cyber"], dependencies=[Depends(require_auth)])


class CyberRequest(BaseModel):
    features: list[float]


_model_path = Path("models") / "cyber" / "supervised" / "cyber_model.pkl"
_cyber_model = joblib.load(_model_path) if _model_path.exists() else None


@router.post("")
def predict_cyber(req: CyberRequest):
    if _cyber_model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Cyber model not found."
        )
    try:
        X = np.array(req.features, dtype=float).reshape(1, -1)
        if hasattr(_cyber_model, "predict_proba"):
            score = float(_cyber_model.predict_proba(X)[0][1])
        elif hasattr(_cyber_model, "decision_function"):
            score = float(_cyber_model.decision_function(X)[0])
        else:
            score = float(_cyber_model.predict(X)[0])
        return {"score": score}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cyber inference failed: {exc}",
        )
