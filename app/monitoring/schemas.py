from typing import Dict, Any, Optional
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
    window: str
    risk_score: float
    details: Dict[str, Any]

class RiskLogEvent(BaseModel):
    timestamp: str
    request_id: str
    scenario: str
    payload: Dict[str, Any]
    risk_scores: Dict[str, float]
    decision: str