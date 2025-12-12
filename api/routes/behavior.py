from pathlib import Path

import joblib
import numpy as np
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from api.deps import require_auth

router = APIRouter(prefix="/api/behavior", tags=["behavior"], dependencies=[Depends(require_auth)])


class BehaviorRequest(BaseModel):
    features: list[float]


_beh_path = Path("models") / "behavior" / "behavior_lof.pkl"
_behavior = joblib.load(_beh_path) if _beh_path.exists() else None
_scaler = _behavior.get("preprocessor") if isinstance(_behavior, dict) else None
_lof = _behavior.get("model") if isinstance(_behavior, dict) else None


@router.post("")
def predict_behavior(req: BehaviorRequest):
    if _scaler is None or _lof is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Behavior model not found."
        )
    try:
        X = np.array(req.features, dtype=float).reshape(1, -1)
        Xs = _scaler.transform(X)
        score = float(_lof.decision_function(Xs)[0])
        return {"score": score}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Behavior inference failed: {exc}",
        )
