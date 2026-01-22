from __future__ import annotations

from typing import List


class SegmentTreeLazy:
    """Segment tree supporting range add and range sum queries."""

    def __init__(self, values: List[float]) -> None:
        if not values:
            raise ValueError("values must not be empty")
        self.n = len(values)
        size = 1
        while size < self.n:
            size <<= 1
        self.size = size
        self.tree = [0.0] * (2 * size)
        self.lazy = [0.0] * (2 * size)
        for idx, val in enumerate(values):
            self.tree[size + idx] = float(val)
        for idx in range(size - 1, 0, -1):
            self.tree[idx] = self.tree[idx * 2] + self.tree[idx * 2 + 1]

    def _push(self, idx: int, seg_len: int) -> None:
        if self.lazy[idx] == 0:
            return
        left = idx * 2
        right = idx * 2 + 1
        add = self.lazy[idx]
        self.lazy[left] += add
        self.lazy[right] += add
        half = seg_len // 2
        self.tree[left] += add * half
        self.tree[right] += add * half
        self.lazy[idx] = 0.0

    def range_add(self, left: int, right: int, value: float) -> None:
        if left < 0 or right < 0 or left > right or right >= self.n:
            raise ValueError("invalid update range")
        self._range_add(1, 0, self.size - 1, left, right, float(value))

    def _range_add(self, idx: int, seg_l: int, seg_r: int, ql: int, qr: int, value: float) -> None:
        if ql <= seg_l and seg_r <= qr:
            self.tree[idx] += value * (seg_r - seg_l + 1)
            self.lazy[idx] += value
            return
        if seg_r < ql or seg_l > qr:
            return
        self._push(idx, seg_r - seg_l + 1)
        mid = (seg_l + seg_r) // 2
        self._range_add(idx * 2, seg_l, mid, ql, qr, value)
        self._range_add(idx * 2 + 1, mid + 1, seg_r, ql, qr, value)
        self.tree[idx] = self.tree[idx * 2] + self.tree[idx * 2 + 1]

    def range_sum(self, left: int, right: int) -> float:
        if left < 0 or right < 0 or left > right or right >= self.n:
            raise ValueError("invalid query range")
        return self._range_sum(1, 0, self.size - 1, left, right)

    def _range_sum(self, idx: int, seg_l: int, seg_r: int, ql: int, qr: int) -> float:
        if ql <= seg_l and seg_r <= qr:
            return self.tree[idx]
        if seg_r < ql or seg_l > qr:
            return 0.0
        self._push(idx, seg_r - seg_l + 1)
        mid = (seg_l + seg_r) // 2
        return self._range_sum(idx * 2, seg_l, mid, ql, qr) + self._range_sum(
            idx * 2 + 1, mid + 1, seg_r, ql, qr
        )
