from __future__ import annotations

from collections import deque
from typing import List, Tuple


class LcaSolver:
    """Binary lifting LCA solver for rooted trees."""

    def __init__(self, n: int, edges: List[Tuple[int, int]], root: int = 0) -> None:
        if n <= 0:
            raise ValueError("n must be positive")
        self.n = n
        self.root = root
        self.log = n.bit_length()
        self.depth = [0] * n
        self.up = [[0] * n for _ in range(self.log)]
        self._build(edges)

    def _build(self, edges: List[Tuple[int, int]]) -> None:
        adj = [[] for _ in range(self.n)]
        for u, v in edges:
            if not (0 <= u < self.n and 0 <= v < self.n):
                raise ValueError("edge node out of range")
            adj[u].append(v)
            adj[v].append(u)

        root = self.root
        if not (0 <= root < self.n):
            raise ValueError("root out of range")

        self.up[0][root] = root
        self.depth[root] = 0
        q: deque[Tuple[int, int]] = deque([(root, root)])
        while q:
            node, parent = q.popleft()
            self.up[0][node] = parent
            for nxt in adj[node]:
                if nxt == parent:
                    continue
                self.depth[nxt] = self.depth[node] + 1
                q.append((nxt, node))

        for k in range(1, self.log):
            for v in range(self.n):
                self.up[k][v] = self.up[k - 1][self.up[k - 1][v]]

    def query(self, u: int, v: int) -> int:
        if not (0 <= u < self.n and 0 <= v < self.n):
            raise ValueError("query node out of range")
        if self.depth[u] < self.depth[v]:
            u, v = v, u

        diff = self.depth[u] - self.depth[v]
        for k in range(self.log):
            if diff & (1 << k):
                u = self.up[k][u]

        if u == v:
            return u

        for k in range(self.log - 1, -1, -1):
            if self.up[k][u] != self.up[k][v]:
                u = self.up[k][u]
                v = self.up[k][v]

        return self.up[0][u]
