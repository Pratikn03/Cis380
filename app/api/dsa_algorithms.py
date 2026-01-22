from __future__ import annotations

from typing import List, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.dsa_algorithms.graph_algorithms import (
    WeightedEdge as GraphWeightedEdge,
    bfs,
    dijkstra,
    dfs,
    kruskal_mst,
    scc_kosaraju,
)
from app.dsa_algorithms.dp_algorithms import coin_change_min, knapsack_01, lis_length
from app.dsa_algorithms.lca import LcaSolver
from app.dsa_algorithms.min_cost_max_flow import min_cost_max_flow
from app.dsa_algorithms.segment_tree import SegmentTreeLazy
from app.dsa_algorithms.segment_tree_queries import SegmentTreeMin
from app.dsa_algorithms.shortest_paths import bellman_ford, floyd_warshall, zero_one_bfs
from app.dsa_algorithms.trie import Trie

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
    model_config = {"populate_by_name": True}
    type: Literal["add", "sum"]
    left: int = Field(..., ge=0, alias="l")
    right: int = Field(..., ge=0, alias="r")
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
            if op.left > op.right:
                raise ValueError("left must be <= right")
            if op.type == "add":
                if op.value is None:
                    raise ValueError("add operation requires value")
                tree.range_add(op.left, op.right, op.value)
            else:
                value = tree.range_sum(op.left, op.right)
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


class SegmentTreeMinOp(BaseModel):
    model_config = {"populate_by_name": True}
    type: Literal["set", "min"]
    left: int = Field(..., ge=0, alias="l")
    right: int = Field(..., ge=0, alias="r")
    value: Optional[float] = None


class SegmentTreeMinRequest(BaseModel):
    values: List[float]
    ops: List[SegmentTreeMinOp]


@router.post("/algorithms/segment-tree-min")
def run_segment_tree_min(payload: SegmentTreeMinRequest) -> dict[str, object]:
    if not payload.values:
        raise HTTPException(status_code=400, detail="values must not be empty")
    try:
        tree = SegmentTreeMin(payload.values)
        results = []
        for idx, op in enumerate(payload.ops):
            if op.left > op.right:
                raise ValueError("left must be <= right")
            if op.type == "set":
                if op.value is None:
                    raise ValueError("set operation requires value")
                if op.left != op.right:
                    raise ValueError("set operation requires left == right (point update)")
                tree.update(op.left, op.value)
            else:
                value = tree.range_min(op.left, op.right)
                results.append({"op_index": idx, "value": value})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"results": results, "ops": len(payload.ops)}


class GraphEdge(BaseModel):
    u: int
    v: int
    w: float = 1.0


class GraphTraversalRequest(BaseModel):
    n: int = Field(..., ge=1, le=200000)
    edges: List[GraphEdge]
    start: int
    directed: bool = False


@router.post("/algorithms/bfs")
def solve_bfs(payload: GraphTraversalRequest) -> dict[str, object]:
    try:
        result = bfs(
            payload.n,
            [GraphWeightedEdge(e.u, e.v, e.w) for e in payload.edges],
            payload.start,
            directed=payload.directed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


@router.post("/algorithms/dfs")
def solve_dfs(payload: GraphTraversalRequest) -> dict[str, object]:
    try:
        result = dfs(
            payload.n,
            [GraphWeightedEdge(e.u, e.v, e.w) for e in payload.edges],
            payload.start,
            directed=payload.directed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


class ShortestPathRequest(BaseModel):
    n: int = Field(..., ge=1, le=200000)
    edges: List[GraphEdge]
    source: int
    directed: bool = False


@router.post("/algorithms/shortest-paths")
def solve_shortest_paths(payload: ShortestPathRequest) -> dict[str, object]:
    try:
        result = dijkstra(
            payload.n,
            [GraphWeightedEdge(e.u, e.v, e.w) for e in payload.edges],
            payload.source,
            directed=payload.directed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


@router.post("/algorithms/shortest-paths/bellman-ford")
def solve_bellman_ford(payload: ShortestPathRequest) -> dict[str, object]:
    try:
        result = bellman_ford(
            payload.n,
            [GraphWeightedEdge(e.u, e.v, e.w) for e in payload.edges],
            payload.source,
            directed=payload.directed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


class FloydWarshallRequest(BaseModel):
    n: int = Field(..., ge=1, le=400)
    edges: List[GraphEdge]
    directed: bool = False


@router.post("/algorithms/shortest-paths/floyd-warshall")
def solve_floyd_warshall(payload: FloydWarshallRequest) -> dict[str, object]:
    try:
        result = floyd_warshall(
            payload.n,
            [GraphWeightedEdge(e.u, e.v, e.w) for e in payload.edges],
            directed=payload.directed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


@router.post("/algorithms/shortest-paths/zero-one-bfs")
def solve_zero_one_bfs(payload: ShortestPathRequest) -> dict[str, object]:
    try:
        result = zero_one_bfs(
            payload.n,
            [GraphWeightedEdge(e.u, e.v, e.w) for e in payload.edges],
            payload.source,
            directed=payload.directed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


class MstRequest(BaseModel):
    n: int = Field(..., ge=1, le=200000)
    edges: List[GraphEdge]


@router.post("/algorithms/mst")
def solve_mst(payload: MstRequest) -> dict[str, object]:
    try:
        result = kruskal_mst(payload.n, [GraphWeightedEdge(e.u, e.v, e.w) for e in payload.edges])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


class SccRequest(BaseModel):
    n: int = Field(..., ge=1, le=200000)
    edges: List[GraphEdge]


@router.post("/algorithms/scc")
def solve_scc(payload: SccRequest) -> dict[str, object]:
    try:
        result = scc_kosaraju(payload.n, [GraphWeightedEdge(e.u, e.v, e.w) for e in payload.edges])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


class TopologicalSortRequest(BaseModel):
    n: int = Field(..., ge=1, le=200000)
    edges: List[EdgePair]


@router.post("/algorithms/topological-sort")
def solve_topological_sort(payload: TopologicalSortRequest) -> dict[str, object]:
    try:
        n = payload.n
        adj = [[] for _ in range(n)]
        in_degree = [0] * n
        for e in payload.edges:
            if not (0 <= e.u < n and 0 <= e.v < n):
                raise ValueError(f"Node index out of bounds: {e.u} or {e.v} (n={n})")
            adj[e.u].append(e.v)
            in_degree[e.v] += 1

        queue = [i for i in range(n) if in_degree[i] == 0]
        result = []
        head = 0

        while head < len(queue):
            u = queue[head]
            head += 1
            result.append(u)

            for v in adj[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)

        if len(result) != n:
            return {"status": "cycle_detected", "result": []}

        return {"status": "success", "result": result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class TrieOp(BaseModel):
    op: Literal["insert", "search", "starts_with", "delete"]
    text: str


class TrieRequest(BaseModel):
    operations: List[TrieOp]


@router.post("/algorithms/trie")
def run_trie(payload: TrieRequest) -> dict[str, object]:
    trie = Trie()
    results = []
    for idx, op in enumerate(payload.operations):
        text = op.text
        if op.op == "insert":
            trie.insert(text)
            results.append({"op_index": idx, "op": op.op, "result": True})
        elif op.op == "search":
            results.append({"op_index": idx, "op": op.op, "result": trie.search(text)})
        elif op.op == "starts_with":
            results.append({"op_index": idx, "op": op.op, "result": trie.starts_with(text)})
        else:
            results.append({"op_index": idx, "op": op.op, "result": trie.delete(text)})
    return {"results": results, "ops": len(payload.operations)}


class DpRequest(BaseModel):
    method: Literal["lis", "knapsack", "coin_change"]
    nums: Optional[List[int]] = None
    weights: Optional[List[int]] = None
    values: Optional[List[int]] = None
    capacity: Optional[int] = None
    coins: Optional[List[int]] = None
    amount: Optional[int] = None


@router.post("/algorithms/dp")
def run_dp(payload: DpRequest) -> dict[str, object]:
    try:
        if payload.method == "lis":
            if payload.nums is None:
                raise ValueError("nums is required for LIS")
            result = lis_length(payload.nums)
            return {"method": "lis", "result": result}
        if payload.method == "knapsack":
            if payload.weights is None or payload.values is None or payload.capacity is None:
                raise ValueError("weights, values, capacity are required for knapsack")
            result = knapsack_01(payload.weights, payload.values, payload.capacity)
            return {"method": "knapsack", "result": result}
        if payload.method == "coin_change":
            if payload.coins is None or payload.amount is None:
                raise ValueError("coins and amount are required for coin_change")
            result = coin_change_min(payload.coins, payload.amount)
            return {"method": "coin_change", "result": result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"method": payload.method, "result": None}
