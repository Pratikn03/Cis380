"""DSA code snippets for offline reference."""

from __future__ import annotations

from collections import deque
import heapq


class SegmentTreeLazy:
    def __init__(self, arr):
        self.n = len(arr)
        self.size = 1
        while self.size < self.n:
            self.size *= 2
        self.tree = [0] * (2 * self.size)
        self.lazy = [0] * (2 * self.size)
        for i, v in enumerate(arr):
            self.tree[self.size + i] = v
        for i in range(self.size - 1, 0, -1):
            self.tree[i] = self.tree[2 * i] + self.tree[2 * i + 1]

    def _apply(self, idx, seg_len, val):
        self.tree[idx] += val * seg_len
        self.lazy[idx] += val

    def _push(self, idx, seg_len):
        if self.lazy[idx] != 0:
            half = seg_len // 2
            self._apply(2 * idx, half, self.lazy[idx])
            self._apply(2 * idx + 1, half, self.lazy[idx])
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


class LCA:
    def __init__(self, n, tree, root=0):
        self.n = n
        self.LOG = (n).bit_length()
        self.up = [[-1] * n for _ in range(self.LOG)]
        self.depth = [0] * n
        self._dfs(root, -1, tree)
        for k in range(1, self.LOG):
            for v in range(n):
                mid = self.up[k - 1][v]
                self.up[k][v] = -1 if mid == -1 else self.up[k - 1][mid]

    def _dfs(self, root, parent, tree):
        stack = [(root, parent)]
        while stack:
            u, p = stack.pop()
            self.up[0][u] = p
            for v in tree[u]:
                if v == p:
                    continue
                self.depth[v] = self.depth[u] + 1
                stack.append((v, u))

    def lca(self, u, v):
        if self.depth[u] < self.depth[v]:
            u, v = v, u
        diff = self.depth[u] - self.depth[v]
        for k in range(self.LOG):
            if diff & (1 << k):
                u = self.up[k][u]
        if u == v:
            return u
        for k in reversed(range(self.LOG)):
            if self.up[k][u] != self.up[k][v]:
                u = self.up[k][u]
                v = self.up[k][v]
        return self.up[0][u]


class TrieNode:
    def __init__(self):
        self.children = {}
        self.end = False


class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str):
        node = self.root
        for ch in word:
            node = node.children.setdefault(ch, TrieNode())
        node.end = True

    def search(self, word: str) -> bool:
        node = self.root
        for ch in word:
            if ch not in node.children:
                return False
            node = node.children[ch]
        return node.end


class MinCostMaxFlow:
    def __init__(self, n):
        self.n = n
        self.g = [[] for _ in range(n)]

    def add_edge(self, u, v, cap, cost):
        self.g[u].append([v, cap, cost, len(self.g[v])])
        self.g[v].append([u, 0, -cost, len(self.g[u]) - 1])

    def flow(self, s, t):
        n = self.n
        res_cost = 0
        res_flow = 0
        pot = [0] * n
        INF = 10**18
        while True:
            dist = [INF] * n
            prev_v = [-1] * n
            prev_e = [-1] * n
            dist[s] = 0
            pq = [(0, s)]
            while pq:
                d, u = heapq.heappop(pq)
                if d != dist[u]:
                    continue
                for i, e in enumerate(self.g[u]):
                    v, cap, cost, _ = e
                    if cap <= 0:
                        continue
                    nd = d + cost + pot[u] - pot[v]
                    if nd < dist[v]:
                        dist[v] = nd
                        prev_v[v] = u
                        prev_e[v] = i
                        heapq.heappush(pq, (nd, v))
            if dist[t] == INF:
                break
            for v in range(n):
                if dist[v] < INF:
                    pot[v] += dist[v]
            add = INF
            v = t
            while v != s:
                u = prev_v[v]
                e = self.g[u][prev_e[v]]
                add = min(add, e[1])
                v = u
            v = t
            while v != s:
                u = prev_v[v]
                e = self.g[u][prev_e[v]]
                e[1] -= add
                rev = e[3]
                self.g[v][rev][1] += add
                v = u
            res_flow += add
            res_cost += add * pot[t]
        return res_flow, res_cost


def lis_length(nums):
    tails = []
    for x in nums:
        i = 0
        j = len(tails)
        while i < j:
            mid = (i + j) // 2
            if tails[mid] < x:
                i = mid + 1
            else:
                j = mid
        if i == len(tails):
            tails.append(x)
        else:
            tails[i] = x
    return len(tails)
