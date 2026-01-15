# Trie Compression (Radix Tree)

A radix tree compresses chains of single-child nodes.
Each edge stores a string label instead of a single character.

Benefits:
- Fewer nodes, lower memory.
- Still supports prefix queries.

Operations (L = length of word):
- Insert: O(L)
- Search: O(L)

```python
class RadixNode:
    def __init__(self):
        self.children = {}  # edge_label -> RadixNode
        self.end = False

class RadixTrie:
    def __init__(self):
        self.root = RadixNode()

    def insert(self, word: str) -> None:
        node = self.root
        while word:
            for edge, child in list(node.children.items()):
                # find common prefix
                i = 0
                while i < len(edge) and i < len(word) and edge[i] == word[i]:
                    i += 1
                if i == 0:
                    continue
                # split edge if partial match
                if i < len(edge):
                    mid = RadixNode()
                    mid.children[edge[i:]] = child
                    node.children[edge[:i]] = mid
                    del node.children[edge]
                    child = mid
                node = child
                word = word[i:]
                break
            else:
                node.children[word] = RadixNode()
                node = node.children[word]
                word = ""
        node.end = True
```

Pitfalls:
- Be careful when splitting edges.
- Need end markers for exact matches.
