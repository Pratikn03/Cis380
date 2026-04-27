"""Fraud risk scoring on a transaction payload."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.agent.tools._base import Tool, ToolError, ToolExecutionContext, ToolResult


class FraudScoreInput(BaseModel):
    transaction_amount: float = Field(..., ge=0.0, description="Amount in USD.")
    device_known: bool = Field(True, description="Recognised device fingerprint.")
    login_country: str = Field("US", description="ISO country code.")
    login_time: float = Field(12.0, ge=0.0, le=23.99, description="Hour of day.")


class FraudScoreOutput(BaseModel):
    fraud_risk: float
    severity: str
    details: dict[str, Any]


class FraudScoreTool(Tool):
    name = "fraud_score"
    description = (
        "Estimate the probability that a single transaction is fraudulent. "
        "Returns a 0-1 risk score plus low/medium/high severity. Use for "
        "single-transaction reviews; for full session risk see ``risk_score``."
    )
    input_schema = FraudScoreInput
    output_schema = FraudScoreOutput

    def _run(self, ctx: ToolExecutionContext, args: FraudScoreInput) -> ToolResult:
        try:
            from app.services.risk_engine import analyze_risk
        except Exception as exc:
            raise ToolError(f"fraud_score unavailable: {exc}") from exc

        payload = {
            "transaction_amount": args.transaction_amount,
            "device_known": args.device_known,
            "login_country": args.login_country,
            "login_time": args.login_time,
            "clicks_per_minute": 10.0,
            "files_accessed": 0,
        }
        scores = analyze_risk(payload)
        score = float(scores.get("fraud_risk", 0.0))
        severity = "high" if score > 0.7 else "medium" if score > 0.4 else "low"
        out = FraudScoreOutput(fraud_risk=score, severity=severity, details=scores)
        return ToolResult(
            summary=f"fraud_risk={score:.2f} severity={severity}",
            data=out.model_dump(),
            confidence=score,
        )
