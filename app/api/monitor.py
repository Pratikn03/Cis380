from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.monitoring.schemas import DriftReport, FraudLogEvent, RiskSummary
from app.monitoring.logger import read_last_n_jsonl
from app.monitoring.service import (
    FRAUD_LOG_PATH,
    RISK_LOG_PATH,
    get_monitor_summary,
    get_drift_report,
    get_risk_summary,
    log_fraud_event,
    ensure_baseline_exists_or_create,
)

router = APIRouter(prefix="/monitor")


@router.post("/log")
async def log_event(event: FraudLogEvent) -> Dict[str, str]:
    log_fraud_event(event)
    return {"status": "logged"}


@router.get("/summary")
async def summary(window_n: int = 1000) -> Dict[str, object]:
    return get_monitor_summary(window_n)


@router.get("/drift")
async def drift(window_n: int = 1000) -> DriftReport:
    return DriftReport(**get_drift_report(window_n))


@router.get("/risk_summary")
async def risk_summary(window_n: int = 1000) -> RiskSummary:
    return RiskSummary(**get_risk_summary(window_n))


@router.get("/events")
async def events(kind: str = "risk", window_n: int = 100) -> Dict[str, object]:
    """Return last N raw monitoring events (demo/debug).

    kind:
      - "risk"  -> `data/monitoring/logs/risk_events.jsonl`
      - "fraud" -> `data/monitoring/logs/fraud_events.jsonl`
    """

    kind_norm = (kind or "").strip().lower()
    if kind_norm not in {"risk", "fraud"}:
        raise HTTPException(status_code=400, detail="kind must be 'risk' or 'fraud'")
    path = RISK_LOG_PATH if kind_norm == "risk" else FRAUD_LOG_PATH
    return {"kind": kind_norm, "path": str(path), "events": read_last_n_jsonl(path, int(window_n))}


class BaselineRequest(BaseModel):
    events_n: int = 2000
    samples: Optional[List[Dict[str, float]]] = None


@router.post("/baseline/build")
async def build_baseline(payload: BaselineRequest) -> Dict[str, str]:
    ensure_baseline_exists_or_create(payload.samples)
    return {"status": "baseline ready"}
