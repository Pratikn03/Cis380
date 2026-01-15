# Strongly Connected Components (SCC)

- In directed graph, SCC is a maximal set where each node reaches every other.

Algorithms:
- Kosaraju: two DFS passes + transpose graph. O(V + E).
- Tarjan: single DFS with low-link values. O(V + E).

Use cases:
- Detect cycles, compress graph to DAG.

Pitfalls:
- Need directed edges; undirected SCCs are just connected components.
