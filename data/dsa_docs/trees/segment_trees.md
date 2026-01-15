# Segment Trees

- Data structure for range queries and point updates.
- Common queries: range sum, min, max.

Build:
- O(n) time, O(n) space.

Operations:
- Point update: O(log n)
- Range query: O(log n)

Variants:
- Lazy propagation for range updates (range add, range assign).

Pitfalls:
- Indexing off-by-one for [l, r] vs [l, r).
- Use 4n array size for safe allocation.
