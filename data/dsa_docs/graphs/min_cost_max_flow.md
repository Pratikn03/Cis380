# Min-Cost Max-Flow

Goal: push maximum flow with minimum total cost.
Each edge has capacity and cost.

Algorithm (successive shortest augmenting path):
1) Maintain residual graph.
2) Repeatedly find shortest path (by cost) from s to t.
3) Augment flow along that path.

With potentials (Johnson trick):
- Use Dijkstra with reduced costs to handle negative edges.

Complexities:
- Edmonds-Karp style: O(F * V * E) for integer capacities.
- Dijkstra + potentials is faster in practice.

```python
class Edge:
    def __init__(self, v, cap, cost, rev):
        self.v = v
        self.cap = cap
        self.cost = cost
        self.rev = rev

class MinCostMaxFlow:
    def __init__(self, n):
        self.n = n
        self.g = [[] for _ in range(n)]

    def add_edge(self, u, v, cap, cost):
        self.g[u].append(Edge(v, cap, cost, len(self.g[v])))
        self.g[v].append(Edge(u, 0, -cost, len(self.g[u]) - 1))

    def flow(self, s, t):
        n = self.n
        res_cost = 0
        res_flow = 0
        pot = [0] * n
        INF = 10**18
        import heapq
        while True:
            dist = [INF] * n
            prev_v = [-1] * n
            prev_e = [-1] * n
            dist[s] = 0
            pq = [(0, s)]
            while pq:
                d, u = heapq.heappop(pq)
                if d != dist[u]:
                    continue
                for i, e in enumerate(self.g[u]):
                    if e.cap <= 0:
                        continue
                    nd = d + e.cost + pot[u] - pot[e.v]
                    if nd < dist[e.v]:
                        dist[e.v] = nd
                        prev_v[e.v] = u
                        prev_e[e.v] = i
                        heapq.heappush(pq, (nd, e.v))
            if dist[t] == INF:
                break
            for v in range(n):
                if dist[v] < INF:
                    pot[v] += dist[v]
            # find bottleneck
            add = INF
            v = t
            while v != s:
                u = prev_v[v]
                e = self.g[u][prev_e[v]]
                add = min(add, e.cap)
                v = u
            # augment
            v = t
            while v != s:
                u = prev_v[v]
                e = self.g[u][prev_e[v]]
                e.cap -= add
                self.g[v][e.rev].cap += add
                v = u
            res_flow += add
            res_cost += add * pot[t]
        return res_flow, res_cost
```

Pitfalls:
- Always add reverse edges with negative cost.
- Use 64-bit ints for large costs/capacities.
