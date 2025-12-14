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
_cyber_model = None
_cyber_model_error: str | None = None


def _get_cyber_model():
    global _cyber_model, _cyber_model_error

    if _cyber_model is not None:
        return _cyber_model
    if not _model_path.exists():
        return None
    if _cyber_model_error is not None:
        return None

    try:
        _cyber_model = joblib.load(_model_path)
    except Exception as exc:  # pragma: no cover - depends on local env
        _cyber_model_error = str(exc)
        return None
    return _cyber_model


@router.post("")
def predict_cyber(req: CyberRequest):
    cyber_model = _get_cyber_model()
    if cyber_model is None:
        detail = "Cyber model not found."
        if _model_path.exists() and _cyber_model_error:
            detail = f"Cyber model failed to load: {_cyber_model_error}"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        )
    try:
        expected = int(getattr(cyber_model, "n_features_in_", 0) or 0)
        feats = list(req.features)
        if expected:
            feats = (feats + [0.0] * expected)[:expected]
        X = np.array(feats, dtype=float).reshape(1, -1)

        if hasattr(cyber_model, "predict_proba"):
            score = float(cyber_model.predict_proba(X)[0][1])
        elif hasattr(cyber_model, "decision_function"):
            score = float(cyber_model.decision_function(X)[0])
        else:
            score = float(cyber_model.predict(X)[0])
        return {"score": score, "input_features": len(req.features), "expected_features": expected or None}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cyber inference failed: {exc}",
        )
