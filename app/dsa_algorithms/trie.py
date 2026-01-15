from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class TrieNode:
    children: Dict[str, "TrieNode"] = field(default_factory=dict)
    is_end: bool = False


class Trie:
    def __init__(self) -> None:
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        node = self.root
        for ch in word:
            node = node.children.setdefault(ch, TrieNode())
        node.is_end = True

    def search(self, word: str) -> bool:
        node = self._walk(word)
        return bool(node and node.is_end)

    def starts_with(self, prefix: str) -> bool:
        return self._walk(prefix) is not None

    def delete(self, word: str) -> bool:
        stack = []
        node = self.root
        for ch in word:
            if ch not in node.children:
                return False
            stack.append((node, ch))
            node = node.children[ch]
        if not node.is_end:
            return False
        node.is_end = False
        for parent, ch in reversed(stack):
            child = parent.children[ch]
            if child.is_end or child.children:
                break
            del parent.children[ch]
        return True

    def _walk(self, text: str) -> TrieNode | None:
        node = self.root
        for ch in text:
            node = node.children.get(ch)
            if node is None:
                return None
        return node


__all__ = ["Trie", "TrieNode"]
