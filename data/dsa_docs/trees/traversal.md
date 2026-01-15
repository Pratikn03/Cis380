# Tree Traversals

Depth-first:
- Preorder: root, left, right (useful for copying tree).
- Inorder: left, root, right (BST sorted output).
- Postorder: left, right, root (useful for delete/free).

Breadth-first:
- Level-order: queue, process level by level.
- Variants: zigzag, right-to-left, level averages.

Iterative tips:
- Use a stack for DFS.
- For inorder, push left path, then visit, then right.
