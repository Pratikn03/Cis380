from __future__ import annotations

from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Dict, List, Optional
from uuid import uuid4

from app.monitoring.baseline import build_baseline_stats, load_baseline, save_baseline
from app.monitoring.drift import compute_drift
from app.monitoring.logger import append_jsonl, read_last_n_jsonl
from app.monitoring.metrics import compute_metrics
from app.monitoring.schemas import DriftReport, FraudLogEvent

LOG_PATH = Path("data/monitoring/logs/fraud_events.jsonl")


def log_fraud_event(event: FraudLogEvent) -> None:
    append_jsonl(LOG_PATH, event.model_dump())


def get_monitor_summary(window_n: int = 1000) -> Dict[str, object]:
    return compute_metrics(LOG_PATH, window_n)


def get_drift_report(window_n: int = 1000) -> Dict[str, object]:
    live_events = read_last_n_jsonl(LOG_PATH, window_n)
    numeric_events = [
        {k: float(v) for k, v in entry.get("features_summary", {}).items() if isinstance(v, (int, float))}
        for entry in live_events
    ]
    baseline_stats = load_baseline()
    report = compute_drift(baseline_stats, numeric_events, window=f"last_{window_n}")
    return report.model_dump()


def ensure_baseline_exists_or_create(sample_events: Optional[List[Dict[str, float]]] = None) -> None:
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
