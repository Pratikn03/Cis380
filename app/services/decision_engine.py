from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Decision = Literal["ALLOW", "STEP_UP_AUTH", "BLOCK"]

ReasonCode = Literal["FRAUD_HIGH", "COMBINED_RISK_HIGH", "LOW_RISK"]


@dataclass(frozen=True)
class DecisionResult:
    decision: Decision
    reason_code: ReasonCode


def make_decision(cyber_risk: float, behavior_risk: float, fraud_risk: float) -> DecisionResult:
    if fraud_risk > 0.85:
        return DecisionResult(decision="BLOCK", reason_code="FRAUD_HIGH")
    if cyber_risk > 0.70 and behavior_risk > 0.60:
        return DecisionResult(decision="STEP_UP_AUTH", reason_code="COMBINED_RISK_HIGH")
    return DecisionResult(decision="ALLOW", reason_code="LOW_RISK")
