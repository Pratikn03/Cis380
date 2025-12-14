from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, List


class MemoryStore:
    """Lightweight in-memory memory per user."""

    def __init__(self, max_turns: int = 10) -> None:
        self._store: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_turns))

    def add_turn(self, user_id: str, user_text: str, assistant_text: str) -> None:
        self._store[user_id].append({"user": user_text, "assistant": assistant_text})

    def get_history(self, user_id: str) -> List[Dict[str, str]]:
        return list(self._store.get(user_id, []))
