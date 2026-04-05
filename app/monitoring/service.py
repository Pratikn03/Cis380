from __future__ import annotations

from pathlib import Path
from statistics import mean
from typing import Dict, List, Optional

from app.monitoring.baseline import build_baseline_stats, load_baseline, save_baseline
from app.monitoring.drift import compute_drift
from app.monitoring.logger import append_jsonl, read_last_n_jsonl
from app.monitoring.metrics import compute_metrics
from app.monitoring.schemas import FraudLogEvent, RiskLogEvent

FRAUD_LOG_PATH = Path("data/monitoring/logs/fraud_events.jsonl")
RISK_LOG_PATH = Path("data/monitoring/logs/risk_events.jsonl")


def log_fraud_event(event: FraudLogEvent) -> None:
    append_jsonl(FRAUD_LOG_PATH, event.model_dump())


def log_risk_event(event: RiskLogEvent) -> None:
    append_jsonl(RISK_LOG_PATH, event.model_dump())


def get_monitor_summary(window_n: int = 1000) -> Dict[str, object]:
    fraud_metrics = compute_metrics(FRAUD_LOG_PATH, window_n)
    risk_metrics = get_risk_summary(window_n)
    return {
        **fraud_metrics,
        "risk": risk_metrics,
        "paths": {
            "fraud_log": str(FRAUD_LOG_PATH),
            "risk_log": str(RISK_LOG_PATH),
        },
    }


def get_risk_summary(window_n: int = 1000) -> Dict[str, object]:
    events = read_last_n_jsonl(RISK_LOG_PATH, window_n)
    decision_counts: Dict[str, int] = {}
    risk_acc: Dict[str, list[float]] = {
        "cyber_risk": [],
        "behavior_risk": [],
        "fraud_risk": [],
        "fusion_risk": [],
    }
    for event in events:
        decision = event.get("decision")
        if decision:
            decision_counts[decision] = decision_counts.get(decision, 0) + 1
        scores = event.get("risk_scores", {})
        for key in risk_acc:
            value = scores.get(key)
            if isinstance(value, (int, float)):
                risk_acc[key].append(float(value))
    avg_risks = {k: (mean(v) if v else 0.0) for k, v in risk_acc.items()}
    return {
        "window_n": int(window_n),
        "total_events": len(events),
        "decision_counts": decision_counts,
        "avg_risks": avg_risks,
    }


def get_drift_report(window_n: int = 1000) -> Dict[str, object]:
    live_events = read_last_n_jsonl(FRAUD_LOG_PATH, window_n)
    numeric_events = [
        {
            k: float(v)
            for k, v in entry.get("features_summary", {}).items()
            if isinstance(v, (int, float))
        }
        for entry in live_events
    ]
    baseline_stats = load_baseline()
    report = compute_drift(baseline_stats, numeric_events, window=f"last_{window_n}")
    return report.model_dump()


def ensure_baseline_exists_or_create(
    sample_events: Optional[List[Dict[str, float]]] = None,
) -> None:
    existing = load_baseline()
    if existing:
        return
    events = sample_events or []
    if not events:
        events = [
            {"amount": 100.0, "hour": 12, "score": 0.1},
        ]
    stats = build_baseline_stats(events)
    save_baseline(stats)
