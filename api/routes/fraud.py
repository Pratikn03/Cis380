from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from pathlib import Path
import numpy as np
import joblib

from api.deps import require_auth

router = APIRouter(prefix="/api/fraud", tags=["fraud"], dependencies=[Depends(require_auth)])


class FraudRequest(BaseModel):
    features: list[float]


_model_path = Path("models") / "fraud" / "supervised" / "fraud_model.pkl"
_fraud_model = joblib.load(_model_path) if _model_path.exists() else None


@router.post("")
def predict_fraud(req: FraudRequest):
    if _fraud_model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Fraud model not found."
        )
    try:
        X = np.array(req.features, dtype=float).reshape(1, -1)
        if hasattr(_fraud_model, "predict_proba"):
            score = float(_fraud_model.predict_proba(X)[0][1])
        elif hasattr(_fraud_model, "decision_function"):
            score = float(_fraud_model.decision_function(X)[0])
        else:
            score = float(_fraud_model.predict(X)[0])
        return {"score": score}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fraud inference failed: {exc}",
        )
