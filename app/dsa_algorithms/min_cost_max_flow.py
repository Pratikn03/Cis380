from __future__ import annotations

import heapq
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class _Edge:
    to: int
    rev: int
    cap: int
    cost: int


def _add_edge(graph: List[List[_Edge]], u: int, v: int, cap: int, cost: int) -> None:
    graph[u].append(_Edge(v, len(graph[v]), cap, cost))
    graph[v].append(_Edge(u, len(graph[u]) - 1, 0, -cost))


def min_cost_max_flow(
    n: int,
    edges: List[Tuple[int, int, int, int]],
    source: int,
    sink: int,
    max_flow: int | None = None,
) -> Tuple[int, int]:
    if n <= 0:
        raise ValueError("n must be positive")
    if not (0 <= source < n and 0 <= sink < n):
        raise ValueError("source/sink out of range")

    graph: List[List[_Edge]] = [[] for _ in range(n)]
    for u, v, cap, cost in edges:
        if cap < 0:
            raise ValueError("capacity must be non-negative")
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError("edge node out of range")
        _add_edge(graph, u, v, int(cap), int(cost))

    flow = 0
    cost = 0
    max_flow_value = max_flow if max_flow is not None else 10**18
    potential = [0] * n

    while flow < max_flow_value:
        dist = [10**18] * n
        prev_v = [-1] * n
        prev_e = [-1] * n
        dist[source] = 0
        heap: list[tuple[int, int]] = [(0, source)]

        while heap:
            cur_dist, v = heapq.heappop(heap)
            if cur_dist != dist[v]:
                continue
            for i, e in enumerate(graph[v]):
                if e.cap <= 0:
                    continue
                nd = cur_dist + e.cost + potential[v] - potential[e.to]
                if nd < dist[e.to]:
                    dist[e.to] = nd
                    prev_v[e.to] = v
                    prev_e[e.to] = i
                    heapq.heappush(heap, (nd, e.to))

        if dist[sink] == 10**18:
            break

        for v in range(n):
            if dist[v] < 10**18:
                potential[v] += dist[v]

        add_flow = max_flow_value - flow
        v = sink
        path_cost = 0
        while v != source:
            pv = prev_v[v]
            pe = prev_e[v]
            if pv == -1 or pe == -1:
                raise RuntimeError("Failed to reconstruct augmenting path")
            edge = graph[pv][pe]
            add_flow = min(add_flow, edge.cap)
            path_cost += edge.cost
            v = pv

        v = sink
        while v != source:
            pv = prev_v[v]
            pe = prev_e[v]
            edge = graph[pv][pe]
            edge.cap -= add_flow
            graph[v][edge.rev].cap += add_flow
            v = pv

        flow += add_flow
        cost += add_flow * path_cost

    return flow, cost
