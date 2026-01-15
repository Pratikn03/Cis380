# Max Flow (Flow Networks)

- Directed graph with capacities on edges.
- Goal: maximum flow from source to sink.

Algorithms:
- Edmonds-Karp (BFS on residual): O(V * E^2)
- Dinic (level graph + blocking flow): O(E * V^2) worst-case, faster in practice.

Key ideas:
- Residual graph tracks remaining capacity.
- Augmenting paths increase total flow.

Pitfalls:
- Use 64-bit ints if capacities are large.
- Always update reverse edges in residual graph.
