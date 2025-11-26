"""Heuristic rules to map scores to recommended actions."""
from __future__ import annotations

from typing import Tuple


def assign_action_from_scores(
    fraud_score: float | None,
    cyber_score: float | None,
    behavior_score: float | None,
    fusion_score: float | None,
    *,
    hi: float = 0.85,
    med: float = 0.65,
    lo: float = 0.50,
) -> Tuple[str, str]:
    """Return (action, reason) based on score thresholds.

    Actions: BLOCK > REVIEW > MONITOR > ALLOW
    """
    scores = {
        "fusion": fusion_score,
        "fraud": fraud_score,
        "cyber": cyber_score,
        "behavior": behavior_score,
    }
    present = {k: v for k, v in scores.items() if v is not None}
    if not present:
        return "MONITOR", "No scores provided; defaulting to MONITOR."

    max_dom, max_val = max(present.items(), key=lambda kv: kv[1])
    if max_val >= hi:
        return "BLOCK", f"High {max_dom} score ({max_val:.3f}) exceeds {hi}."
    if max_val >= med:
        return "REVIEW", f"Elevated {max_dom} score ({max_val:.3f}) exceeds {med}."
    if max_val >= lo:
        return "MONITOR", f"Moderate {max_dom} score ({max_val:.3f}) exceeds {lo}."
    return "ALLOW", f"Scores below threshold; max {max_dom}={max_val:.3f}."


__all__ = ["assign_action_from_scores"]
