from __future__ import annotations

from pathlib import Path

import pytest

from app.monitoring.logger import append_jsonl
from app.monitoring.schemas import FraudLogEvent, RiskSummary
from app.monitoring import service


def _configure_monitor_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(service, "FRAUD_LOG_PATH", tmp_path / "fraud_events.jsonl")
    monkeypatch.setattr(service, "RISK_LOG_PATH", tmp_path / "risk_events.jsonl")


def test_monitor_workflow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_monitor_paths(monkeypatch, tmp_path)

    service.log_fraud_event(
        FraudLogEvent(
            timestamp="2025-12-12T00:00:00Z",
            request_id="test-1",
            user_id="tester",
            model_version="fraud_v1",
            features_summary={"amount": 120.0, "hour": 10},
            prediction_score=0.2,
            prediction_label="low",
            latency_ms=20.0,
        )
    )

    summary = service.get_monitor_summary(window_n=10)
    assert "count" in summary
    service.ensure_baseline_exists_or_create([{"amount": 120.0, "hour": 10.0, "score": 0.2}])
    drift = service.get_drift_report(window_n=10)
    assert "drift_score" in drift and "status" in drift


def test_risk_summary_empty_contract(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_monitor_paths(monkeypatch, tmp_path)
    payload = RiskSummary(**service.get_risk_summary(window_n=25)).model_dump()

    assert payload["window_n"] == 25
    assert payload["total_events"] == 0
    assert payload["decision_counts"] == {}
    assert payload["avg_risks"] == {
        "cyber_risk": 0.0,
        "behavior_risk": 0.0,
        "fraud_risk": 0.0,
        "fusion_risk": 0.0,
    }


def test_risk_summary_populated_contract(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_monitor_paths(monkeypatch, tmp_path)
    risk_log = tmp_path / "risk_events.jsonl"

    append_jsonl(
        risk_log,
        {
            "timestamp": "2026-02-20T01:00:00Z",
            "request_id": "risk-1",
            "scenario": "login",
            "payload": {"device_known": False},
            "risk_scores": {
                "cyber_risk": 0.8,
                "behavior_risk": 0.2,
                "fraud_risk": 0.4,
                "fusion_risk": 0.6,
            },
            "decision": "review",
        },
    )
    append_jsonl(
        risk_log,
        {
            "timestamp": "2026-02-20T01:01:00Z",
            "request_id": "risk-2",
            "scenario": "payment",
            "payload": {"transaction_amount": 900},
            "risk_scores": {
                "cyber_risk": 0.4,
                "behavior_risk": 0.6,
                "fraud_risk": 0.8,
                "fusion_risk": 0.7,
            },
            "decision": "block",
        },
    )

    payload = RiskSummary(**service.get_risk_summary(window_n=100)).model_dump()
    assert payload["window_n"] == 100
    assert payload["total_events"] == 2
    assert payload["decision_counts"] == {"review": 1, "block": 1}
    assert payload["avg_risks"]["cyber_risk"] == pytest.approx(0.6)
    assert payload["avg_risks"]["behavior_risk"] == pytest.approx(0.4)
    assert payload["avg_risks"]["fraud_risk"] == pytest.approx(0.6)
    assert payload["avg_risks"]["fusion_risk"] == pytest.approx(0.65)
