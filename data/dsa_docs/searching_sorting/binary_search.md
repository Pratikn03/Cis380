# Binary Search

Binary search works on sorted arrays/lists and reduces the search space by half.

Template:
- lo = 0, hi = n - 1
- while lo <= hi:
  - mid = (lo + hi) // 2
  - move lo/hi based on comparison

Complexity: O(log n) time, O(1) space.

Variants:
- first/last occurrence
- lower_bound / upper_bound
- search on monotonic predicate
