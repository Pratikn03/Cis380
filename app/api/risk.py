from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter
import logging
from pydantic import BaseModel, Field

router = APIRouter(tags=["risk"])
logger = logging.getLogger(__name__)


class RiskPayload(BaseModel):
    login_country: str = Field(default="US")
    device_known: bool = Field(default=True)
    login_time: float = Field(default=12.0, description="Hour of day in 0-23")
    clicks_per_minute: float = Field(default=10.0)
    files_accessed: int = Field(default=0)
    transaction_amount: float = Field(default=0.0)


def _clamp(value: float) -> float:
    return float(min(max(value, 0.0), 1.0))


def _risk_from_payload(payload_data: dict[str, Any]) -> dict[str, float]:
    amount = float(payload_data.get("transaction_amount", 0.0) or 0.0)
    clicks = float(payload_data.get("clicks_per_minute", 0.0) or 0.0)
    files = float(payload_data.get("files_accessed", 0.0) or 0.0)
    login_time = float(payload_data.get("login_time", 12.0) or 12.0)
    device_known = bool(payload_data.get("device_known", True))
    login_country = str(payload_data.get("login_country") or "").upper()

    after_hours = 1.0 if login_time < 6 or login_time > 22 else 0.0
    high_risk_country = 1.0 if login_country in {"NG", "BR", "AE"} else 0.0
    unknown_device = 0.0 if device_known else 1.0

    cyber_risk = _clamp((clicks / 200.0) * 0.55 + (files / 200.0) * 0.35 + after_hours * 0.10)
    behavior_risk = _clamp(after_hours * 0.45 + unknown_device * 0.35 + (clicks / 200.0) * 0.20)
    fraud_risk = _clamp((amount / 10000.0) * 0.65 + unknown_device * 0.25 + high_risk_country * 0.10)
    fusion_risk = _clamp(cyber_risk * 0.34 + behavior_risk * 0.33 + fraud_risk * 0.33)
    return {
        "cyber_risk": cyber_risk,
        "behavior_risk": behavior_risk,
        "fraud_risk": fraud_risk,
        "fusion_risk": fusion_risk,
    }


def _decision_for_scores(cyber_risk: float, behavior_risk: float, fraud_risk: float) -> tuple[str, str]:
    if fraud_risk > 0.85:
        return "BLOCK", "FRAUD_HIGH"
    if cyber_risk > 0.70 and behavior_risk > 0.60:
        return "STEP_UP_AUTH", "COMBINED_RISK_HIGH"
    return "ALLOW", "LOW_RISK"


@router.post("/risk/analyze")
def risk_analyze(payload: RiskPayload, explain: bool = True) -> dict[str, Any]:
    payload_data = payload.model_dump()
    scores = _risk_from_payload(payload_data)
    decision_value, reason_code = _decision_for_scores(
        scores["cyber_risk"],
        scores["behavior_risk"],
        scores["fraud_risk"],
    )

    out: dict[str, Any] = {
        "cyber_risk": scores["cyber_risk"],
        "behavior_risk": scores["behavior_risk"],
        "fraud_risk": scores["fraud_risk"],
        "fusion_risk": scores["fusion_risk"],
        "decision": decision_value,
        "reason_code": reason_code,
    }

    if explain:
        out["explanation"] = (
            f"Decision={decision_value} ({reason_code}) with "
            f"cyber={scores['cyber_risk']:.3f}, behavior={scores['behavior_risk']:.3f}, "
            f"fraud={scores['fraud_risk']:.3f}, fusion={scores['fusion_risk']:.3f}. "
            f"Signals: login_country={payload.login_country}, device_known={payload.device_known}, "
            f"transaction_amount={payload.transaction_amount}."
        )

    # Monitoring (best effort): keep logging even if shapes change.
    logged = False
    try:  # pragma: no cover
        from app.monitoring.schemas import RiskLogEvent
        from app.monitoring.service import log_risk_event

        log_risk_event(
            RiskLogEvent(
                timestamp=datetime.utcnow().isoformat() + "Z",
                request_id=str(uuid4()),
                scenario=payload.login_country,
                payload=payload_data,
                risk_scores={
                    "cyber_risk": scores["cyber_risk"],
                    "behavior_risk": scores["behavior_risk"],
                    "fraud_risk": scores["fraud_risk"],
                    "fusion_risk": scores["fusion_risk"],
                },
                decision=decision_value,
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
