from __future__ import annotations

from typing import List, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.dsa_algorithms.lca import LcaSolver
from app.dsa_algorithms.min_cost_max_flow import min_cost_max_flow
from app.dsa_algorithms.segment_tree import SegmentTreeLazy

router = APIRouter(prefix="/api/dsa", tags=["dsa-algorithms"])


class EdgePair(BaseModel):
    u: int
    v: int


class LcaRequest(BaseModel):
    n: int = Field(..., ge=1, le=200000)
    edges: List[EdgePair]
    root: int = 0
    queries: List[EdgePair]


class LcaResponse(BaseModel):
    lca: List[int]


@router.post("/algorithms/lca", response_model=LcaResponse)
def solve_lca(payload: LcaRequest) -> LcaResponse:
    if len(payload.edges) == 0:
        raise HTTPException(status_code=400, detail="edges must not be empty")
    try:
        solver = LcaSolver(
            payload.n,
            [(e.u, e.v) for e in payload.edges],
            root=payload.root,
        )
        results = [solver.query(q.u, q.v) for q in payload.queries]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return LcaResponse(lca=results)


class SegmentOp(BaseModel):
    type: Literal["add", "sum"]
    l: int = Field(..., ge=0)
    r: int = Field(..., ge=0)
    value: Optional[float] = None


class SegmentTreeRequest(BaseModel):
    values: List[float]
    ops: List[SegmentOp]


@router.post("/algorithms/segment-tree")
def run_segment_tree(payload: SegmentTreeRequest) -> dict[str, object]:
    if not payload.values:
        raise HTTPException(status_code=400, detail="values must not be empty")
    try:
        tree = SegmentTreeLazy(payload.values)
        results = []
        for idx, op in enumerate(payload.ops):
            if op.l > op.r:
                raise ValueError("l must be <= r")
            if op.type == "add":
                if op.value is None:
                    raise ValueError("add operation requires value")
                tree.range_add(op.l, op.r, op.value)
            else:
                value = tree.range_sum(op.l, op.r)
                results.append({"op_index": idx, "value": value})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"results": results, "ops": len(payload.ops)}


class FlowEdge(BaseModel):
    u: int
    v: int
    cap: int = Field(..., ge=0)
    cost: int


class MinCostMaxFlowRequest(BaseModel):
    n: int = Field(..., ge=1, le=100000)
    edges: List[FlowEdge]
    source: int
    sink: int
    max_flow: Optional[int] = Field(default=None, ge=1)


@router.post("/algorithms/min-cost-max-flow")
def solve_min_cost_max_flow(payload: MinCostMaxFlowRequest) -> dict[str, int]:
    if payload.source == payload.sink:
        raise HTTPException(status_code=400, detail="source and sink must differ")
    try:
        flow, cost = min_cost_max_flow(
            payload.n,
            [(e.u, e.v, e.cap, e.cost) for e in payload.edges],
            payload.source,
            payload.sink,
            max_flow=payload.max_flow,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"flow": int(flow), "cost": int(cost)}
