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


class FraudExplainRequest(FraudRequest):
    sample_id: int = 0


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


def _model_input(fraud_model, features: list[float]):
    import numpy as np
    import pandas as pd

    cols = list(getattr(fraud_model, "feature_names_in_", []))
    if cols:
        values = [0.0] * len(cols)
        for index, value in enumerate(features[: len(cols)]):
            values[index] = float(value)
        return pd.DataFrame([values], columns=cols), cols

    expected = int(getattr(fraud_model, "n_features_in_", 0) or len(features) or 1)
    values = (list(features) + [0.0] * expected)[:expected]
    return np.array(values, dtype=float).reshape(1, -1), [f"feature_{i}" for i in range(expected)]


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
        x_data, feature_names = _model_input(fraud_model, features)
        expected_features = len(feature_names)

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


@router.post("/fraud/explain")
async def fraud_explain(payload: FraudExplainRequest):
    fraud_model = _get_fraud_model()
    if fraud_model is None:
        detail = "Fraud model not found."
        if _MODEL_PATH.exists() and _fraud_model_error:
            detail = f"Fraud model failed to load: {_fraud_model_error}"
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)

    features = _feature_values(payload)
    try:
        import numpy as np

        x_data, feature_names = _model_input(fraud_model, features)
        if hasattr(x_data, "to_numpy"):
            sample = x_data.to_numpy(dtype=float)
        else:
            sample = np.asarray(x_data, dtype=float)

        degraded = False
        try:
            from dashboard.components.shap_viz import SHAPExplainer

            background = np.zeros((1, sample.shape[1]), dtype=float)
            explainer = SHAPExplainer(
                fraud_model,
                background_data=background,
                feature_names=feature_names,
                max_background_samples=1,
            )
            explanation = explainer.explain_single(sample[0], sample_id=payload.sample_id).to_dict()
            degraded = not bool(explanation.get("feature_contributions"))
        except Exception as exc:
            degraded = True
            values = sample[0].tolist()
            contributions = dict(zip(feature_names, values))
            ranked = sorted(contributions.items(), key=lambda item: abs(item[1]), reverse=True)
            explanation = {
                "sample_id": payload.sample_id,
                "prediction": None,
                "base_value": None,
                "feature_contributions": contributions,
                "top_positive": [(k, v) for k, v in ranked if v > 0][:5],
                "top_negative": [(k, v) for k, v in ranked if v < 0][:5],
                "error": str(exc),
            }

        score_response = await fraud_endpoint(payload)
        return {
            "score": score_response.get("score"),
            "risk": score_response.get("risk"),
            "feature_names": feature_names,
            "explanation": explanation,
            "degraded": degraded,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Fraud explanation failed: {exc}") from exc
