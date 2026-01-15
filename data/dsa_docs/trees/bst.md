# Binary Search Trees (BST)

- BST property: left subtree < node < right subtree (by key).
- Search/insert/delete: O(h) time, where h is tree height.
- Balanced BST: h = O(log n). Skewed BST: h = O(n).

Common operations:
- Find min: go left until null.
- Find max: go right until null.
- Inorder traversal yields sorted order.

Pitfalls:
- Duplicates: define policy (left or right).
- Deletion cases: leaf, one child, two children (swap with successor/predecessor).
