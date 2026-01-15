from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class WeightedEdge:
    u: int
    v: int
    w: float


def build_adj(n: int, edges: List[WeightedEdge], directed: bool) -> List[List[Tuple[int, float]]]:
    adj: List[List[Tuple[int, float]]] = [[] for _ in range(n)]
    for edge in edges:
        if not (0 <= edge.u < n and 0 <= edge.v < n):
            raise ValueError("edge node out of range")
        adj[edge.u].append((edge.v, edge.w))
        if not directed:
            adj[edge.v].append((edge.u, edge.w))
    return adj


def bfs(n: int, edges: List[WeightedEdge], start: int, directed: bool = False) -> dict[str, object]:
    if not (0 <= start < n):
        raise ValueError("start node out of range")
    adj = build_adj(n, edges, directed)
    dist = [-1] * n
    order: List[int] = []
    q: deque[int] = deque([start])
    dist[start] = 0
    while q:
        u = q.popleft()
        order.append(u)
        for v, _ in adj[u]:
            if dist[v] == -1:
                dist[v] = dist[u] + 1
                q.append(v)
    return {"order": order, "distances": dist}


def dfs(n: int, edges: List[WeightedEdge], start: int, directed: bool = False) -> dict[str, object]:
    if not (0 <= start < n):
        raise ValueError("start node out of range")
    adj = build_adj(n, edges, directed)
    visited = [False] * n
    order: List[int] = []
    stack = [start]
    while stack:
        u = stack.pop()
        if visited[u]:
            continue
        visited[u] = True
        order.append(u)
        # push neighbors in reverse for stable ordering
        for v, _ in reversed(adj[u]):
            if not visited[v]:
                stack.append(v)
    return {"order": order}


def dijkstra(
    n: int,
    edges: List[WeightedEdge],
    source: int,
    directed: bool = False,
) -> dict[str, object]:
    if not (0 <= source < n):
        raise ValueError("source node out of range")
    adj = build_adj(n, edges, directed)
    dist = [float("inf")] * n
    parent = [-1] * n
    dist[source] = 0.0
    import heapq

    heap: list[tuple[float, int]] = [(0.0, source)]
    while heap:
        d, u = heapq.heappop(heap)
        if d != dist[u]:
            continue
        for v, w in adj[u]:
            nd = d + float(w)
            if nd < dist[v]:
                dist[v] = nd
                parent[v] = u
                heapq.heappush(heap, (nd, v))
    return {"distances": dist, "parent": parent}


class _DSU:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> bool:
        ra = self.find(a)
        rb = self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


def kruskal_mst(n: int, edges: List[WeightedEdge]) -> dict[str, object]:
    dsu = _DSU(n)
    total = 0.0
    mst_edges: list[dict[str, object]] = []
    for edge in sorted(edges, key=lambda e: e.w):
        if dsu.union(edge.u, edge.v):
            total += float(edge.w)
            mst_edges.append({"u": edge.u, "v": edge.v, "w": float(edge.w)})
    return {"total_weight": total, "edges": mst_edges}


def scc_kosaraju(n: int, edges: List[WeightedEdge]) -> dict[str, object]:
    adj = build_adj(n, edges, directed=True)
    rev_adj: List[List[int]] = [[] for _ in range(n)]
    for edge in edges:
        rev_adj[edge.v].append(edge.u)

    visited = [False] * n
    order: List[int] = []

    def dfs1(start: int) -> None:
        stack = [(start, 0)]
        while stack:
            node, idx = stack.pop()
            if idx == 0:
                if visited[node]:
                    continue
                visited[node] = True
            if idx < len(adj[node]):
                stack.append((node, idx + 1))
                nxt, _ = adj[node][idx]
                if not visited[nxt]:
                    stack.append((nxt, 0))
            else:
                order.append(node)

    for v in range(n):
        if not visited[v]:
            dfs1(v)

    comp_id = [-1] * n
    components: List[List[int]] = []

    def dfs2(start: int, cid: int) -> None:
        stack = [start]
        comp_id[start] = cid
        while stack:
            node = stack.pop()
            for nxt in rev_adj[node]:
                if comp_id[nxt] == -1:
                    comp_id[nxt] = cid
                    stack.append(nxt)

    for v in reversed(order):
        if comp_id[v] == -1:
            cid = len(components)
            dfs2(v, cid)
            comp_nodes = [i for i, c in enumerate(comp_id) if c == cid]
            components.append(comp_nodes)

    return {"components": components, "component_id": comp_id}


__all__ = [
    "WeightedEdge",
    "bfs",
    "dfs",
    "dijkstra",
    "kruskal_mst",
    "scc_kosaraju",
]
