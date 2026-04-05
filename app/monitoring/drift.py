from __future__ import annotations

from typing import Dict, List

from app.monitoring.schemas import DriftReport
from app.monitoring.status import BLOCKED, DEGRADED, READY


def psi(baseline: List[float], current: List[float], bins: int = 5) -> float:
    import numpy as np

    if not baseline or not current:
        return 0.0
    edges = np.linspace(
        min(min(baseline), min(current)), max(max(baseline), max(current)), bins + 1
    )

    def freq(values):
        hist, _ = np.histogram(values, bins=edges)
        probs = hist / max(hist.sum(), 1)
        probs[probs == 0] = 1e-6
        return probs

    base = freq(baseline)
    curr = freq(current)
    return float(np.sum((base - curr) * np.log(base / curr)))


def classify_status(score: float) -> str:
    if score < 0.1:
        return "ok"
    if score < 0.25:
        return "warning"
    return "critical"


def classify_readiness_status(score: float) -> str:
    if score < 0.1:
        return READY
    if score < 0.25:
        return DEGRADED
    return BLOCKED


def compute_drift(
    baseline: Dict[str, Dict[str, float]], live_events: List[Dict[str, float]], window: str
) -> DriftReport:
    aggregated: Dict[str, List[float]] = {}
    for event in live_events:
        for feature, value in event.items():
            aggregated.setdefault(feature, []).append(float(value))
    drift_scores: Dict[str, float] = {}
    for feature, values in aggregated.items():
        base_values = []
        if feature in baseline and baseline[feature].get("mean") is not None:
            base_values = [baseline[feature]["mean"]] * len(values)
        drift_scores[feature] = psi(base_values, values) if base_values else 0.0
    total_score = sum(drift_scores.values()) / max(len(drift_scores), 1)
    status = classify_status(total_score)
    readiness_status = classify_readiness_status(total_score)
    return DriftReport(
        window=window,
        drift_score=total_score,
        per_feature={k: {"psi": v} for k, v in drift_scores.items()},
        status=status,
        readiness_status=readiness_status,
        blocking=readiness_status == BLOCKED,
    )
