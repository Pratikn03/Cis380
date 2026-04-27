"""Cyber risk scoring (single-dimension)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.agent.tools._base import Tool, ToolError, ToolExecutionContext, ToolResult


class CyberScoreInput(BaseModel):
    clicks_per_minute: float = Field(10.0, ge=0.0)
    files_accessed: int = Field(0, ge=0)
    device_known: bool = Field(True)
    login_time: float = Field(12.0, ge=0.0, le=23.99)
    login_country: str = Field("US")


class CyberScoreOutput(BaseModel):
    cyber_risk: float
    severity: str
    details: dict[str, Any]


class CyberScoreTool(Tool):
    name = "cyber_score"
    description = (
        "Score the cyber risk of a session: malware/intrusion/breach indicators "
        "from device, network, and behaviour signals. Returns a 0-1 score plus "
        "low/medium/high severity."
    )
    input_schema = CyberScoreInput
    output_schema = CyberScoreOutput

    def _run(self, ctx: ToolExecutionContext, args: CyberScoreInput) -> ToolResult:
        try:
            from app.services.risk_engine import analyze_risk
        except Exception as exc:
            raise ToolError(f"cyber_score unavailable: {exc}") from exc

        scores = analyze_risk({**args.model_dump(), "transaction_amount": 0.0})
        score = float(scores.get("cyber_risk", 0.0))
        severity = "high" if score > 0.7 else "medium" if score > 0.4 else "low"
        out = CyberScoreOutput(cyber_risk=score, severity=severity, details=scores)
        return ToolResult(
            summary=f"cyber_risk={score:.2f} severity={severity}",
            data=out.model_dump(),
            confidence=score,
        )
