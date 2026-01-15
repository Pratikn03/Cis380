# Heaps Basics

- Binary heap: complete tree with heap property.
- Min-heap: parent <= children. Max-heap: parent >= children.
- Operations: push/pop in O(log n), peek in O(1).

Use cases:
- Priority queues, top-k elements, Dijkstra.

Pitfalls:
- For top-k smallest, use max-heap of size k.
- For top-k largest, use min-heap of size k.
