# Segment Tree with Lazy Propagation

Lazy propagation handles range updates efficiently.
Example: range add + range sum.

Complexities:
- Build: O(n)
- Range update: O(log n)
- Range query: O(log n)

Key idea:
- Store a lazy value for each node that represents pending updates.
- Push lazy values down only when needed.

```python
# Range add + range sum segment tree
class SegTree:
    def __init__(self, arr):
        self.n = len(arr)
        self.size = 1
        while self.size < self.n:
            self.size *= 2
        self.tree = [0] * (2 * self.size)
        self.lazy = [0] * (2 * self.size)
        for i in range(self.n):
            self.tree[self.size + i] = arr[i]
        for i in range(self.size - 1, 0, -1):
            self.tree[i] = self.tree[2 * i] + self.tree[2 * i + 1]

    def _apply(self, idx, seg_len, val):
        self.tree[idx] += val * seg_len
        self.lazy[idx] += val

    def _push(self, idx, seg_len):
        if self.lazy[idx] != 0:
            mid = seg_len // 2
            self._apply(2 * idx, mid, self.lazy[idx])
            self._apply(2 * idx + 1, mid, self.lazy[idx])
            self.lazy[idx] = 0

    def _update(self, l, r, val, idx, seg_l, seg_r):
        if r <= seg_l or seg_r <= l:
            return
        if l <= seg_l and seg_r <= r:
            self._apply(idx, seg_r - seg_l, val)
            return
        self._push(idx, seg_r - seg_l)
        mid = (seg_l + seg_r) // 2
        self._update(l, r, val, 2 * idx, seg_l, mid)
        self._update(l, r, val, 2 * idx + 1, mid, seg_r)
        self.tree[idx] = self.tree[2 * idx] + self.tree[2 * idx + 1]

    def update(self, l, r, val):
        self._update(l, r, val, 1, 0, self.size)

    def _query(self, l, r, idx, seg_l, seg_r):
        if r <= seg_l or seg_r <= l:
            return 0
        if l <= seg_l and seg_r <= r:
            return self.tree[idx]
        self._push(idx, seg_r - seg_l)
        mid = (seg_l + seg_r) // 2
        return self._query(l, r, 2 * idx, seg_l, mid) + self._query(l, r, 2 * idx + 1, mid, seg_r)

    def query(self, l, r):
        return self._query(l, r, 1, 0, self.size)
```

Pitfalls:
- Use [l, r) intervals consistently.
- Always push before descending on partial overlap.
