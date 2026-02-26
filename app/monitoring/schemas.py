from typing import Dict, Any, Optional, List
from pydantic import BaseModel


class DriftReport(BaseModel):
    window: str
    drift_score: float
    per_feature: Dict[str, Dict[str, float]]
    status: str


class FraudLogEvent(BaseModel):
    timestamp: str
    request_id: str
    user_id: str
    model_version: str
    features_summary: Dict[str, Any]
    prediction_score: float
    prediction_label: str
    latency_ms: float
    ground_truth: Optional[int] = None


class RiskSummary(BaseModel):
    window_n: int
    total_events: int
    decision_counts: Dict[str, int]
    avg_risks: Dict[str, float]


class RiskLogEvent(BaseModel):
    timestamp: str
    request_id: str
    scenario: str
    payload: Dict[str, Any]
    risk_scores: Dict[str, float]
    decision: str


class LogStatusResponse(BaseModel):
    status: str


class MonitorPaths(BaseModel):
    fraud_log: str
    risk_log: str


class MonitorSummaryResponse(BaseModel):
    count: int
    avg_latency: float
    avg_score: float
    label_dist: Dict[str, int]
    risk: RiskSummary
    paths: MonitorPaths


class MonitorEventsResponse(BaseModel):
    kind: str
    path: str
    events: List[Dict[str, Any]]


class BaselineBuildResponse(BaseModel):
    status: str
