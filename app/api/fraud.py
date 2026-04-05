from __future__ import annotations

import time
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.monitoring.schemas import FraudLogEvent
from app.monitoring.service import log_fraud_event

router = APIRouter()


class FraudRequest(BaseModel):
    user_id: str = "anon"
    amount: float = Field(0.0, ge=0)
    channel: str = "web"
    country: str = "us"
    features: dict[str, float] = Field(default_factory=dict)


@router.post("/fraud")
async def fraud_endpoint(payload: FraudRequest):
    start = time.time()
    score = min(1.0, payload.amount / 1000.0)
    if payload.features.get("velocity", 0) > 5:
        score += 0.2
    score = min(score, 1.0)
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
            **payload.features,
        },
        prediction_score=score,
        prediction_label=label,
        latency_ms=latency,
    )
    log_fraud_event(event)
    return {"risk": label, "score": score, "model_version": "fraud_v1"}
