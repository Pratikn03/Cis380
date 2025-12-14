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
_behavior = None
_behavior_error: str | None = None
_scaler = None
_lof = None


def _load_behavior():
    global _behavior, _behavior_error, _scaler, _lof

    if _behavior is not None:
        return
    if not _beh_path.exists():
        return
    if _behavior_error is not None:
        return

    try:
        _behavior = joblib.load(_beh_path)
    except Exception as exc:  # pragma: no cover - depends on local env
        _behavior_error = str(exc)
        return

    if isinstance(_behavior, dict):
        _scaler = _behavior.get("preprocessor")
        _lof = _behavior.get("model")


@router.post("")
def predict_behavior(req: BehaviorRequest):
    _load_behavior()
    if _scaler is None or _lof is None:
        detail = "Behavior model not found."
        if _beh_path.exists() and _behavior_error:
            detail = f"Behavior model failed to load: {_behavior_error}"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        )
    try:
        expected = int(getattr(_scaler, "n_features_in_", 0) or 0)
        feats = list(req.features)
        if expected:
            feats = (feats + [0.0] * expected)[:expected]
        X = np.array(feats, dtype=float).reshape(1, -1)
        Xs = _scaler.transform(X)
        score = float(_lof.decision_function(Xs)[0])
        return {"score": score, "input_features": len(req.features), "expected_features": expected or None}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Behavior inference failed: {exc}",
        )
