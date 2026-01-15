# Minimum Spanning Tree (MST)

- Connect all vertices with minimum total weight.
- Graph must be connected and undirected.

Kruskal:
- Sort edges by weight, add if no cycle (DSU).
- O(E log E)

Prim:
- Grow tree from any node using a min-heap.
- O(E log V)

Pitfalls:
- MST is not defined for directed graphs.
- Multiple MSTs can exist with same weight.
