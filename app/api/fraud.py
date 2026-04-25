from __future__ import annotations

import time
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.monitoring.schemas import FraudLogEvent
from app.monitoring.service import log_fraud_event

router = APIRouter()


class FraudRequest(BaseModel):
    user_id: str = "anon"
    amount: float = Field(0.0, ge=0)
    channel: str = "web"
    country: str = "us"
    features: list[float] | dict[str, float] = Field(default_factory=list)


_MODEL_PATH = Path("models") / "fraud" / "supervised" / "fraud_model.pkl"
_fraud_model = None
_fraud_model_error: str | None = None


def _get_fraud_model():
    global _fraud_model, _fraud_model_error

    if _fraud_model is not None:
        return _fraud_model
    if not _MODEL_PATH.exists():
        return None
    if _fraud_model_error is not None:
        return None
    try:
        import joblib

        _fraud_model = joblib.load(_MODEL_PATH)
    except Exception as exc:  # pragma: no cover - local artifact dependent
        _fraud_model_error = str(exc)
        return None
    return _fraud_model


def _feature_values(payload: FraudRequest) -> list[float]:
    if isinstance(payload.features, dict):
        if payload.features:
            return [float(value) for value in payload.features.values()]
        return [payload.amount, float(payload.features.get("velocity", 0.0))]
    values = [float(value) for value in payload.features]
    return values if values else [payload.amount]


@router.post("/fraud")
async def fraud_endpoint(payload: FraudRequest):
    start = time.time()
    features = _feature_values(payload)
    fraud_model = _get_fraud_model()
    if fraud_model is None:
        detail = "Fraud model not found."
        if _MODEL_PATH.exists() and _fraud_model_error:
            detail = f"Fraud model failed to load: {_fraud_model_error}"
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)

    try:
        import numpy as np
        import pandas as pd

        cols = list(getattr(fraud_model, "feature_names_in_", []))
        if cols:
            values = [0.0] * len(cols)
            for index, value in enumerate(features[: len(cols)]):
                values[index] = float(value)
            x_data = pd.DataFrame([values], columns=cols)
            expected_features = len(cols)
        else:
            expected_features = int(getattr(fraud_model, "n_features_in_", 0) or 0)
            values = list(features)
            if expected_features:
                values = (values + [0.0] * expected_features)[:expected_features]
            x_data = np.array(values, dtype=float).reshape(1, -1)

        if hasattr(fraud_model, "predict_proba"):
            score = float(fraud_model.predict_proba(x_data)[0][1])
        elif hasattr(fraud_model, "decision_function"):
            score = float(fraud_model.decision_function(x_data)[0])
        else:
            score = float(fraud_model.predict(x_data)[0])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Fraud inference failed: {exc}") from exc

    label = "low" if score < 0.33 else "medium" if score < 0.66 else "high"
    latency = (time.time() - start) * 1000
    event = FraudLogEvent(
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        request_id=str(uuid4()),
        user_id=payload.user_id,
        model_version="fraud_v1",
        features_summary={
            "amount": payload.amount,
            "channel": payload.channel,
            "country": payload.country,
            "input_features": len(features),
        },
        prediction_score=score,
        prediction_label=label,
        latency_ms=latency,
    )
    log_fraud_event(event)
    return {
        "risk": label,
        "score": score,
        "input_features": len(features),
        "expected_features": expected_features or None,
        "model_version": "fraud_v1",
    }
