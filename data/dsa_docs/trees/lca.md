# Lowest Common Ancestor (LCA)

The LCA of two nodes u and v in a rooted tree is the deepest node that is an ancestor of both.

## Binary Lifting (most common)

Preprocess parents at powers of two.
- up[k][v] = 2^k-th ancestor of v
- depth[v] = depth from root

Complexities:
- Preprocess: O(n log n)
- Query: O(log n)

Algorithm:
1) Lift the deeper node up to the same depth.
2) Lift both nodes up together from highest power down.
3) The parent of either node is the LCA.

```python
# Example: LCA with binary lifting
LOG = 17  # for n <= 1e5
up = [[-1] * n for _ in range(LOG)]
depth = [0] * n

def dfs(root: int):
    stack = [(root, -1)]
    while stack:
        u, p = stack.pop()
        up[0][u] = p
        for v in tree[u]:
            if v == p:
                continue
            depth[v] = depth[u] + 1
            stack.append((v, u))

    for k in range(1, LOG):
        for v in range(n):
            mid = up[k - 1][v]
            up[k][v] = -1 if mid == -1 else up[k - 1][mid]


def lca(u: int, v: int) -> int:
    if depth[u] < depth[v]:
        u, v = v, u
    # lift u
    diff = depth[u] - depth[v]
    for k in range(LOG):
        if diff & (1 << k):
            u = up[k][u]
    if u == v:
        return u
    # lift both
    for k in reversed(range(LOG)):
        if up[k][u] != up[k][v]:
            u = up[k][u]
            v = up[k][v]
    return up[0][u]
```

## Euler Tour + RMQ (alternative)
- Euler tour list of nodes with depths.
- LCA becomes RMQ over depths between first occurrences.
- Preprocess O(n log n) or O(n) with sparse table.

Pitfalls:
- Always root the tree.
- For undirected edges, skip parent during DFS.
