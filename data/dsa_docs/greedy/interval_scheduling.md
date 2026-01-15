# Interval Scheduling

- Goal: select max number of non-overlapping intervals.
- Greedy strategy: sort by end time, pick earliest finishing.

Proof idea:
- Earliest finish leaves most room for the rest.

Complexities:
- Sort O(n log n), scan O(n).
