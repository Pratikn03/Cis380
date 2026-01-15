# Longest Increasing Subsequence (LIS)

- Given array, find longest strictly increasing subsequence.

DP O(n^2):
- dp[i] = max LIS ending at i.

Binary search O(n log n):
- Maintain tails[] where tails[k] = smallest tail of length k+1.
- For each x, find lower_bound in tails and replace.

Pitfalls:
- For non-decreasing LIS, use upper_bound.
- The tails array gives length, not the actual sequence (unless you track parents).
