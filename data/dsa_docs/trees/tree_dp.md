# DP on Trees (Tree DP)

- Compute values per node based on children/parent.
- Typical patterns: subtree sizes, max path sum, independent set.

Example (subtree size):
- dp[u] = 1 + sum(dp[v]) for children v.

Rerooting:
- Compute answers for all roots using two-pass DP.
- First pass: compute subtree values.
- Second pass: propagate parent contributions.

Complexities:
- Usually O(n) time, O(n) space.

Pitfalls:
- Avoid revisiting parent in undirected trees.
