from __future__ import annotations

import json
import os
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, List


class MemoryStore:
    """Lightweight per-user chat memory with optional persistence."""

    def __init__(self, max_turns: int = 10, persist_path: str | None = None) -> None:
        self._store: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_turns))
        self._persist_path = Path(persist_path) if persist_path else None
        if self._persist_path:
            self._load_from_disk()

    @classmethod
    def from_env(cls) -> "MemoryStore":
        max_turns = int(os.getenv("CHAT_MEMORY_MAX_TURNS", "10"))
        persist = os.getenv("CHAT_MEMORY_PERSIST", "false").lower() == "true"
        path = os.getenv("CHAT_MEMORY_PATH", "data/processed/memory/chat_history.jsonl")
        return cls(max_turns=max_turns, persist_path=path if persist else None)

    def _load_from_disk(self) -> None:
        if not self._persist_path or not self._persist_path.exists():
            return
        try:
            with self._persist_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    try:
                        item = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    user_id = str(item.get("user_id") or "anon")
                    user_text = str(item.get("user") or "")
                    assistant_text = str(item.get("assistant") or "")
                    if user_text or assistant_text:
                        self._store[user_id].append(
                            {"user": user_text, "assistant": assistant_text}
                        )
        except Exception:
            return

    def _persist_turn(self, user_id: str, user_text: str, assistant_text: str) -> None:
        if not self._persist_path:
            return
        self._persist_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "ts": time.time(),
            "user_id": user_id,
            "user": user_text,
            "assistant": assistant_text,
        }
        with self._persist_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")

    def add_turn(self, user_id: str, user_text: str, assistant_text: str) -> None:
        self._store[user_id].append({"user": user_text, "assistant": assistant_text})
        self._persist_turn(user_id, user_text, assistant_text)

    def get_history(self, user_id: str) -> List[Dict[str, str]]:
        return list(self._store.get(user_id, []))
