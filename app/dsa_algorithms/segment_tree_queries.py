from __future__ import annotations

from typing import List


class SegmentTreeMin:
    """Segment tree for range minimum query with point updates."""

    def __init__(self, values: List[float]) -> None:
        if not values:
            raise ValueError("values must not be empty")
        self.n = len(values)
        size = 1
        while size < self.n:
            size <<= 1
        self.size = size
        self.tree = [float("inf")] * (2 * size)
        for idx, val in enumerate(values):
            self.tree[size + idx] = float(val)
        for idx in range(size - 1, 0, -1):
            self.tree[idx] = min(self.tree[idx * 2], self.tree[idx * 2 + 1])

    def update(self, index: int, value: float) -> None:
        if index < 0 or index >= self.n:
            raise ValueError("index out of range")
        pos = self.size + index
        self.tree[pos] = float(value)
        pos //= 2
        while pos >= 1:
            self.tree[pos] = min(self.tree[pos * 2], self.tree[pos * 2 + 1])
            pos //= 2

    def range_min(self, left: int, right: int) -> float:
        if left < 0 or right < 0 or left > right or right >= self.n:
            raise ValueError("invalid query range")
        left += self.size
        right += self.size
        res = float("inf")
        while left <= right:
            if left % 2 == 1:
                res = min(res, self.tree[left])
                left += 1
            if right % 2 == 0:
                res = min(res, self.tree[right])
                right -= 1
            left //= 2
            right //= 2
        return res


__all__ = ["SegmentTreeMin"]
