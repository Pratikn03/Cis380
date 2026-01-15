# Bit Manipulation Basics

- AND (&), OR (|), XOR (^), NOT (~), shifts (<<, >>).
- Check bit: (x >> k) & 1.
- Set bit: x | (1 << k).
- Clear bit: x & ~(1 << k).
- Toggle bit: x ^ (1 << k).

Common tricks:
- x & (x - 1) clears the lowest set bit.
- Count bits: use builtin popcount if available.
