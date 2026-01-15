from __future__ import annotations

from collections import deque
from typing import List, Tuple

from app.dsa_algorithms.graph_algorithms import WeightedEdge, build_adj


def bellman_ford(
    n: int, edges: List[WeightedEdge], source: int, directed: bool = True
) -> dict[str, object]:
    if not (0 <= source < n):
        raise ValueError("source node out of range")
    all_edges: List[Tuple[int, int, float]] = []
    for edge in edges:
        all_edges.append((edge.u, edge.v, edge.w))
        if not directed:
            all_edges.append((edge.v, edge.u, edge.w))

    dist = [float("inf")] * n
    dist[source] = 0.0

    for _ in range(n - 1):
        updated = False
        for u, v, w in all_edges:
            if dist[u] != float("inf") and dist[u] + float(w) < dist[v]:
                dist[v] = dist[u] + float(w)
                updated = True
        if not updated:
            break

    has_negative_cycle = False
    for u, v, w in all_edges:
        if dist[u] != float("inf") and dist[u] + float(w) < dist[v]:
            has_negative_cycle = True
            break

    return {"distances": dist, "negative_cycle": has_negative_cycle}


def floyd_warshall(n: int, edges: List[WeightedEdge], directed: bool = True) -> dict[str, object]:
    dist = [[float("inf")] * n for _ in range(n)]
    for i in range(n):
        dist[i][i] = 0.0
    for edge in edges:
        dist[edge.u][edge.v] = min(dist[edge.u][edge.v], float(edge.w))
        if not directed:
            dist[edge.v][edge.u] = min(dist[edge.v][edge.u], float(edge.w))

    for k in range(n):
        for i in range(n):
            if dist[i][k] == float("inf"):
                continue
            for j in range(n):
                nd = dist[i][k] + dist[k][j]
                if nd < dist[i][j]:
                    dist[i][j] = nd

    return {"distances": dist}


def zero_one_bfs(
    n: int, edges: List[WeightedEdge], source: int, directed: bool = False
) -> dict[str, object]:
    if not (0 <= source < n):
        raise ValueError("source node out of range")
    for edge in edges:
        if edge.w not in (0, 1):
            raise ValueError("0-1 BFS requires weights 0 or 1")
    adj = build_adj(n, edges, directed)
    dist = [float("inf")] * n
    dist[source] = 0.0
    dq: deque[int] = deque([source])
    while dq:
        u = dq.popleft()
        for v, w in adj[u]:
            nd = dist[u] + float(w)
            if nd < dist[v]:
                dist[v] = nd
                if w == 0:
                    dq.appendleft(v)
                else:
                    dq.append(v)
    return {"distances": dist}


__all__ = ["bellman_ford", "floyd_warshall", "zero_one_bfs"]
