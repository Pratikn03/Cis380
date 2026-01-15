# Reversing a Linked List

Iterative approach:
- prev = None, curr = head
- while curr:
  - next_node = curr.next
  - curr.next = prev
  - prev = curr
  - curr = next_node

Complexity: O(n) time, O(1) space.
