from __future__ import annotations

from datetime import datetime
from time import perf_counter
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.risk import RiskPayload, risk_analyze
from app.api.v1.rag import RagQueryRequest, query_rag
from app.db.session import SessionLocal

router = APIRouter(prefix="/internal", tags=["internal"])


class InternalEnvelope(BaseModel):
    correlationId: str = Field(default_factory=lambda: str(uuid4()))
    actor: str = "gateway"
    trace: dict[str, Any] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)


class InternalResponse(BaseModel):
    correlationId: str
    status: str
    output: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)
    errors: list[dict[str, Any]] = Field(default_factory=list)


def _success(correlation_id: str, output: dict[str, Any], latency_ms: float) -> InternalResponse:
    return InternalResponse(
        correlationId=correlation_id,
        status="ok",
        output=output,
        metrics={"latencyMs": round(latency_ms, 2)},
    )


def _failure(correlation_id: str, code: str, message: str, latency_ms: float) -> InternalResponse:
    return InternalResponse(
        correlationId=correlation_id,
        status="error",
        metrics={"latencyMs": round(latency_ms, 2)},
        errors=[{"code": code, "message": message}],
    )


@router.get("/health")
def internal_health() -> dict[str, Any]:
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "sentifargo-internal",
    }


@router.post("/risk/analyze", response_model=InternalResponse)
def internal_risk_analyze(envelope: InternalEnvelope) -> InternalResponse:
    start = perf_counter()
    cid = envelope.correlationId
    try:
        payload = RiskPayload(**envelope.payload)
        output = risk_analyze(payload)
        return _success(cid, output, (perf_counter() - start) * 1000)
    except Exception as exc:
        return _failure(
            cid,
            "INTERNAL_FAILURE",
            f"risk analyze failed: {exc}",
            (perf_counter() - start) * 1000,
        )


@router.post("/rag/query", response_model=InternalResponse)
def internal_rag_query(envelope: InternalEnvelope) -> InternalResponse:
    start = perf_counter()
    cid = envelope.correlationId
    query = str(envelope.payload.get("query") or "").strip()
    if not query:
        return _failure(
            cid,
            "INVALID_INPUT",
            "payload.query is required",
            (perf_counter() - start) * 1000,
        )

    top_k = int(envelope.payload.get("top_k", 6))
    return_chunks = bool(envelope.payload.get("return_chunks", False))

    try:
        req = RagQueryRequest(query=query, top_k=top_k, return_chunks=return_chunks)
        with SessionLocal() as db:
            output = query_rag(req, db=db)
        return _success(cid, output, (perf_counter() - start) * 1000)
    except HTTPException as exc:
        return _failure(
            cid,
            "INVALID_INPUT" if exc.status_code < 500 else "INTERNAL_FAILURE",
            str(exc.detail),
            (perf_counter() - start) * 1000,
        )
    except Exception as exc:
        return _failure(
            cid,
            "INTERNAL_FAILURE",
            f"rag query failed: {exc}",
            (perf_counter() - start) * 1000,
        )
