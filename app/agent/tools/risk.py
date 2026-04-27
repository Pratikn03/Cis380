"""Unified risk score (cyber + behavior + fraud) using app.services.risk_engine."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.agent.tools._base import Tool, ToolError, ToolExecutionContext, ToolResult


class RiskScoreInput(BaseModel):
    transaction_amount: float = Field(0.0, description="Amount in USD.")
    clicks_per_minute: float = Field(10.0, ge=0.0, description="User click rate.")
    files_accessed: int = Field(0, ge=0, description="Number of files accessed in this session.")
    device_known: bool = Field(True, description="True if the device fingerprint is recognised.")
    login_time: float = Field(12.0, ge=0.0, le=23.99, description="Hour of day, 0-23.")
    login_country: str = Field("US", description="ISO country code of login.")


class RiskScoreOutput(BaseModel):
    cyber_risk: float
    behavior_risk: float
    fraud_risk: float
    fusion_score: float | None = None
    decision: str | None = None
    explanation: str | None = None
    details: dict[str, Any]


class RiskScoreTool(Tool):
    name = "risk_score"
    description = (
        "Compute the unified cyber + behavior + fraud risk for a session payload "
        "and return a recommended decision (allow / step_up / block) with a "
        "natural-language explanation."
    )
    input_schema = RiskScoreInput
    output_schema = RiskScoreOutput

    def _run(self, ctx: ToolExecutionContext, args: RiskScoreInput) -> ToolResult:
        try:
            from app.services.decision_engine import make_decision
            from app.services.explainer import explain_decision
            from app.services.risk_engine import analyze_risk
        except Exception as exc:
            raise ToolError(f"risk_score unavailable: {exc}") from exc

        payload = args.model_dump()
        try:
            scores = analyze_risk(payload)
        except Exception as exc:
            raise ToolError(f"analyze_risk failed: {exc}") from exc

        decision_result = make_decision(
            scores.get("cyber_risk", 0.0),
            scores.get("behavior_risk", 0.0),
            scores.get("fraud_risk", 0.0),
        )
        explanation = explain_decision(
            risks=scores,
            decision=decision_result.decision,
            context=[
                f"login_country={args.login_country}",
                f"transaction_amount={args.transaction_amount}",
                f"device_known={args.device_known}",
            ],
        )

        out = RiskScoreOutput(
            cyber_risk=float(scores.get("cyber_risk", 0.0)),
            behavior_risk=float(scores.get("behavior_risk", 0.0)),
            fraud_risk=float(scores.get("fraud_risk", 0.0)),
            fusion_score=float(scores.get("fusion_score")) if scores.get("fusion_score") is not None else None,
            decision=decision_result.decision,
            explanation=explanation,
            details=scores,
        )
        summary = (
            f"decision={out.decision} "
            f"cyber={out.cyber_risk:.2f} behavior={out.behavior_risk:.2f} fraud={out.fraud_risk:.2f}"
        )
        return ToolResult(summary=summary, data=out.model_dump(), confidence=None)
