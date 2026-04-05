from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter
import logging
from pydantic import BaseModel, Field

from app.monitoring.schemas import RiskLogEvent
from app.monitoring.service import log_risk_event
from app.services.decision_engine import make_decision
from app.services.explainer import explain_decision
from app.services.risk_engine import analyze_risk

router = APIRouter(tags=["risk"])
logger = logging.getLogger(__name__)


class RiskPayload(BaseModel):
    login_country: str = Field(default="US")
    device_known: bool = Field(default=True)
    login_time: float = Field(default=12.0, description="Hour of day in 0-23")
    clicks_per_minute: float = Field(default=10.0)
    files_accessed: int = Field(default=0)
    transaction_amount: float = Field(default=0.0)


@router.post("/risk/analyze")
def risk_analyze(payload: RiskPayload, explain: bool = True) -> dict[str, Any]:
    # Changed from async def to def to run in threadpool (CPU-bound task)
    payload_data = payload.model_dump()
    scores = analyze_risk(payload_data)
    decision = make_decision(
        scores.get("cyber_risk", 0.0),
        scores.get("behavior_risk", 0.0),
        scores.get("fraud_risk", 0.0),
    )

    out: dict[str, Any] = {
        "cyber_risk": float(scores.get("cyber_risk", 0.0)),
        "behavior_risk": float(scores.get("behavior_risk", 0.0)),
        "fraud_risk": float(scores.get("fraud_risk", 0.0)),
        "fusion_risk": float(scores.get("fusion_risk", 0.0)),
        "decision": decision.decision,
        "reason_code": decision.reason_code,
    }
    if "fusion_meta" in scores:
        out["fusion_meta"] = scores.get("fusion_meta")
    if "gemini_analysis" in scores:
        out["gemini_analysis"] = scores.get("gemini_analysis")

    if explain:
        out["explanation"] = explain_decision(
            risks={
                "cyber_risk": float(scores.get("cyber_risk", 0.0)),
                "behavior_risk": float(scores.get("behavior_risk", 0.0)),
                "fraud_risk": float(scores.get("fraud_risk", 0.0)),
                "fusion_risk": float(scores.get("fusion_risk", 0.0)),
            },
            decision=decision.decision,
            context=[
                f"login_country={payload.login_country}",
                f"device_known={payload.device_known}",
                f"transaction_amount={payload.transaction_amount}",
            ],
        )

    # Monitoring (best effort): keep logging even if shapes change.
    logged = False
    try:  # pragma: no cover
        log_risk_event(
            RiskLogEvent(
                timestamp=datetime.utcnow().isoformat() + "Z",
                request_id=str(uuid4()),
                scenario=payload.login_country,
                payload=payload_data,
                risk_scores={
                    "cyber_risk": float(scores.get("cyber_risk", 0.0)),
                    "behavior_risk": float(scores.get("behavior_risk", 0.0)),
                    "fraud_risk": float(scores.get("fraud_risk", 0.0)),
                    "fusion_risk": float(scores.get("fusion_risk", 0.0)),
                },
                decision=decision.decision,
            )
        )
        logged = True
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to log risk event: %s", exc)

    out["monitoring"] = {
        "logged": logged,
        "log_path": "data/monitoring/logs/risk_events.jsonl",
    }

    return out
