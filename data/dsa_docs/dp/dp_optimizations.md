# DP Optimizations

## Divide and Conquer Optimization
Applicable when:
- dp[i][j] = min_{k < j} (dp[i-1][k] + cost(k, j))
- The optimal k is monotonic: opt[i][j] <= opt[i][j+1]

Complexity: O(k * n log n)

## Knuth Optimization
Applicable when:
- Quadrangle inequality + monotone opt.
- Transition: dp[i][j] = min_{k in [i, j)} (dp[i][k] + dp[k+1][j]) + cost(i, j)

Complexity: O(n^2)

## Convex Hull Trick (CHT)
Use when transitions are linear:
- dp[i] = min_j (m_j * x_i + b_j)
- Maintain lower hull for monotone x_i.

## DP on Trees
- Use subtree DP + rerooting for all roots.
- Common: max path, independent set.

## Bitset Optimization
- For subset sums, use bitset shifts to get O(n * sum/word).

Pitfalls:
- Always verify monotonicity assumptions.
- Off-by-one in intervals kills correctness.
