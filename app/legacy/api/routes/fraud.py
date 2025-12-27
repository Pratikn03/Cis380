from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..deps import require_auth

router = APIRouter(prefix="/api/fraud", tags=["fraud"], dependencies=[Depends(require_auth)])


class FraudRequest(BaseModel):
    features: list[float]


_model_path = Path("models") / "fraud" / "supervised" / "fraud_model.pkl"
_fraud_model = None
_fraud_model_error: str | None = None


def _get_fraud_model():
    global _fraud_model, _fraud_model_error

    if _fraud_model is not None:
        return _fraud_model
    if not _model_path.exists():
        return None
    if _fraud_model_error is not None:
        return None

    try:
        _fraud_model = joblib.load(_model_path)
    except Exception as exc:  # pragma: no cover - depends on local env
        _fraud_model_error = str(exc)
        return None
    return _fraud_model


@router.post("")
def predict_fraud(req: FraudRequest):
    fraud_model = _get_fraud_model()
    if fraud_model is None:
        detail = "Fraud model not found."
        if _model_path.exists() and _fraud_model_error:
            detail = f"Fraud model failed to load: {_fraud_model_error}"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        )
    try:
        cols = list(getattr(fraud_model, "feature_names_in_", []))
        if cols:
            values = [0.0] * len(cols)
            for i, v in enumerate(req.features[: len(cols)]):
                values[i] = float(v)
            X = pd.DataFrame([values], columns=cols)
        else:
            X = np.array(req.features, dtype=float).reshape(1, -1)

        if hasattr(fraud_model, "predict_proba"):
            score = float(fraud_model.predict_proba(X)[0][1])
        elif hasattr(fraud_model, "decision_function"):
            score = float(fraud_model.decision_function(X)[0])
        else:
            score = float(fraud_model.predict(X)[0])
        return {
            "score": score,
            "input_features": len(req.features),
            "expected_features": len(cols) if cols else None,
            "feature_names": cols or None,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fraud inference failed: {exc}",
        )
