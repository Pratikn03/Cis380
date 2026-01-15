# DP on Trees (Advanced)

Classic problems:
- Tree diameter (longest path).
- Maximum path sum.
- Maximum independent set on tree.

Example (tree diameter):
- DFS to compute top two depths from each node.
- Update global answer with depth1 + depth2.

Example (independent set):
- dp[u][0]: best when u not chosen.
- dp[u][1]: best when u chosen.
- Transition over children.

Pitfalls:
- Tree is undirected; pass parent to avoid cycles.
