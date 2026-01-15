# Priority Queue Patterns

- Maintain k best: push, if size>k then pop.
- Merge k sorted lists using a heap of size k.
- Sliding window median: two heaps (max-heap for left, min-heap for right).

Complexities:
- Insert/remove: O(log n).
- Rebalance two-heaps: O(log n).
