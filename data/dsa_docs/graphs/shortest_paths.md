# Shortest Paths

- Unweighted: BFS from source.
- Non-negative weights: Dijkstra (min-heap). O((V+E) log V).
- Negative weights: Bellman-Ford (O(VE)), detects negative cycles.
- All-pairs: Floyd-Warshall (O(V^3)), for small graphs.

Tip:
- Dijkstra fails with negative edges.
