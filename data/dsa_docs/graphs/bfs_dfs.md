# BFS vs DFS

BFS (queue):
- Shortest path in unweighted graphs.
- Level-by-level traversal.

DFS (stack/recursion):
- Explore deep paths, backtrack.
- Cycle detection, topological ordering.

Pitfalls:
- Mark visited early to avoid re-queueing.
- For directed graphs, track recursion stack to detect cycles.
