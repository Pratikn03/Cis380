from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Any

from pydantic import BaseModel, Field


class FraudLogEvent(BaseModel):
    timestamp: str
    request_id: str
    user_id: str
    model_version: str
    features_summary: Dict[str, Any]
    prediction_score: float
    prediction_label: str
    latency_ms: float


class DriftReport(BaseModel):
    window: str
    drift_score: float
    per_feature: Dict[str, Dict[str, float]]
    status: str
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RiskLogEvent(BaseModel):
    timestamp: str
    request_id: str
    scenario: str | None = None
    payload: Dict[str, Any]
    risk_scores: Dict[str, float]
    decision: str


class RiskSummary(BaseModel):
    total_events: int
    decision_counts: Dict[str, int]
    avg_risks: Dict[str, float]
