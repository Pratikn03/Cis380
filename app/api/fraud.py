from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class FraudRequest(BaseModel):
    user_id: str = "anon"
    amount: float = Field(0.0, ge=0)
    channel: str = "web"
    country: str = "us"
    features: dict[str, float] | list[float] = Field(default_factory=dict)


def _feature_summary(payload: FraudRequest) -> tuple[dict[str, float], int]:
    raw = payload.features
    if isinstance(raw, dict):
        return raw, len(raw)
    if isinstance(raw, list):
        summary = {f"feature_{idx}": float(value) for idx, value in enumerate(raw)}
        return summary, len(raw)
    return {}, 0


@router.post("/fraud")
async def fraud_endpoint(payload: FraudRequest):
    start = time.time()
    feature_map, input_features = _feature_summary(payload)
    inferred_amount = payload.amount
    if not inferred_amount and feature_map:
        inferred_amount = sum(abs(float(v)) for v in feature_map.values()) * 100

    score = min(1.0, inferred_amount / 1000.0)
    if feature_map.get("velocity", 0) > 5:
        score += 0.2
    score = min(score, 1.0)
    label = "low" if score < 0.33 else "medium" if score < 0.66 else "high"
    latency = (time.time() - start) * 1000
    try:
        from app.monitoring.schemas import FraudLogEvent
        from app.monitoring.service import log_fraud_event

        event = FraudLogEvent(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            request_id=str(uuid4()),
            user_id=payload.user_id,
            model_version="fraud_v1",
            features_summary={
                "amount": inferred_amount,
                "channel": payload.channel,
                "country": payload.country,
                **feature_map,
            },
            prediction_score=score,
            prediction_label=label,
            latency_ms=latency,
        )
        log_fraud_event(event)
    except Exception:
        pass
    return {
        "risk": label,
        "score": score,
        "model_version": "fraud_v1",
        "input_features": input_features,
        "expected_features": None,
    }
