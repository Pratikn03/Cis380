from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.monitoring.schemas import DriftReport, FraudLogEvent
from app.monitoring.service import (
    get_monitor_summary,
    get_drift_report,
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


class BaselineRequest(BaseModel):
    events_n: int = 2000
    samples: Optional[List[Dict[str, float]]] = None


@router.post("/baseline/build")
async def build_baseline(payload: BaselineRequest) -> Dict[str, str]:
    ensure_baseline_exists_or_create(payload.samples)
    return {"status": "baseline ready"}
