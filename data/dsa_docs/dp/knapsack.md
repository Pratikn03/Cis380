# 0/1 Knapsack (Classic DP)

- Given weights w[i], values v[i], capacity C.
- State: dp[i][c] = max value using first i items with capacity c.
- Transition:
  - skip i: dp[i-1][c]
  - take i: dp[i-1][c - w[i]] + v[i]

Optimization:
- Use 1D dp[c] and iterate c from C down to w[i].
