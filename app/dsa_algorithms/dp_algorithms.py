from __future__ import annotations

from bisect import bisect_left
from typing import List


def lis_length(nums: List[int]) -> int:
    """Longest increasing subsequence length (O(n log n))."""
    tails: List[int] = []
    for num in nums:
        idx = bisect_left(tails, num)
        if idx == len(tails):
            tails.append(num)
        else:
            tails[idx] = num
    return len(tails)


def knapsack_01(weights: List[int], values: List[int], capacity: int) -> int:
    """0/1 knapsack with rolling array optimization."""
    if capacity < 0:
        raise ValueError("capacity must be >= 0")
    if len(weights) != len(values):
        raise ValueError("weights and values length mismatch")
    dp = [0] * (capacity + 1)
    for w, v in zip(weights, values):
        if w < 0:
            raise ValueError("weights must be non-negative")
        for c in range(capacity, w - 1, -1):
            dp[c] = max(dp[c], dp[c - w] + v)
    return dp[capacity]


def coin_change_min(coins: List[int], amount: int) -> int:
    """Minimum coins to reach amount; returns -1 if not possible."""
    if amount < 0:
        raise ValueError("amount must be >= 0")
    if amount == 0:
        return 0
    max_val = amount + 1
    dp = [max_val] * (amount + 1)
    dp[0] = 0
    for coin in coins:
        if coin <= 0:
            raise ValueError("coin values must be positive")
        for a in range(coin, amount + 1):
            dp[a] = min(dp[a], dp[a - coin] + 1)
    return dp[amount] if dp[amount] != max_val else -1


__all__ = ["lis_length", "knapsack_01", "coin_change_min"]
