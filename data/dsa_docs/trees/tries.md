# Tries (Prefix Trees)

- Trie stores strings by characters along edges.
- Each node represents a prefix; children keyed by next character.
- Used for prefix search, autocomplete, dictionary checks.

Operations (L = length of word):
- Insert: O(L)
- Search: O(L)
- StartsWith: O(L)

Memory:
- Large if alphabet is big. Use maps or compressed tries to reduce size.

Pitfalls:
- Need end-of-word marker to distinguish "app" vs "apple".
- Case sensitivity and character normalization matter.
