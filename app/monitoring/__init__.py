from __future__ import annotations

try:  # pragma: no cover - optional runtime imports
    from app.monitoring.service import (
        ensure_baseline_exists_or_create,
        get_drift_report,
        get_monitor_summary,
        log_fraud_event,
    )
except Exception:  # pragma: no cover - keep lightweight imports working in scripts
    ensure_baseline_exists_or_create = None
    get_drift_report = None
    get_monitor_summary = None
    log_fraud_event = None

__all__ = [
    "log_fraud_event",
    "get_monitor_summary",
    "get_drift_report",
    "ensure_baseline_exists_or_create",
]
