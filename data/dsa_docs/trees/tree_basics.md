# Trees Basics

- Tree: connected acyclic graph with a root, parent/child edges.
- Terms: root, leaf, depth, height, subtree.
- Binary tree: each node has up to two children (left/right).
- Full/complete/perfect are different structural properties.

Complexities (n = nodes):
- Traversals: O(n) time, O(h) space for recursion (h = height).

Common patterns:
- Preorder: process, left, right.
- Inorder: left, process, right.
- Postorder: left, right, process.
- Level-order: BFS with queue.

Pitfalls:
- Recursive depth can be O(n) for skewed trees.
- Always handle null/empty children.
