from __future__ import annotations

from typing import Any

__all__ = ["analyze_risk", "make_decision", "explain_decision"]


def __getattr__(name: str) -> Any:
    if name == "analyze_risk":
        from app.services.risk_engine import analyze_risk

        return analyze_risk
    if name == "make_decision":
        from app.services.decision_engine import make_decision

        return make_decision
    if name == "explain_decision":
        from app.services.explainer import explain_decision

        return explain_decision
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
