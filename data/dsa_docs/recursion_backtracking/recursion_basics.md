# Recursion Basics

- A function that calls itself until a base case.
- Good for tree/graph traversal, divide-and-conquer.

Tips:
- Always define a base case.
- Be careful with recursion depth (stack overflow).

Example pattern:
- Solve(n) = combine(Solve(n-1), Solve(n-2)).
