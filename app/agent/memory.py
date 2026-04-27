from __future__ import annotations

import json
import logging
import os
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Dict, List, Optional

_log = logging.getLogger("Sentifargo.agent.memory")


class Blackboard:
    """Cross-agent shared state, keyed by session_id then slot.

    Backed by Redis when ``REDIS_URL`` is reachable; falls back to a
    process-local dict otherwise (good enough for tests and for offline mode).
    Values are JSON-serialised so the same blackboard can be read by any
    worker that shares the Redis connection.
    """

    KEY_PREFIX = "agent:bb:"
    DEFAULT_TTL_SECONDS = 3600

    def __init__(self, redis_url: Optional[str] = None, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        self._ttl = ttl_seconds
        self._fallback: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._redis = None
        if redis_url:
            try:
                import redis  # type: ignore

                client = redis.Redis.from_url(redis_url, decode_responses=True)
                client.ping()
                self._redis = client
            except Exception as exc:
                _log.warning("Blackboard falling back to in-memory: %s", exc)
                self._redis = None

    @classmethod
    def from_env(cls) -> "Blackboard":
        return cls(
            redis_url=os.getenv("REDIS_URL"),
            ttl_seconds=int(os.getenv("AGENT_BLACKBOARD_TTL_SECONDS", str(cls.DEFAULT_TTL_SECONDS))),
        )

    @property
    def is_redis(self) -> bool:
        return self._redis is not None

    def _key(self, session_id: str) -> str:
        return f"{self.KEY_PREFIX}{session_id}"

    def get(self, session_id: str, slot: str, default: Any = None) -> Any:
        if self._redis is not None:
            raw = self._redis.hget(self._key(session_id), slot)
            if raw is None:
                return default
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return raw
        return self._fallback[session_id].get(slot, default)

    def set(self, session_id: str, slot: str, value: Any) -> None:
        payload = json.dumps(value, default=str)
        if self._redis is not None:
            key = self._key(session_id)
            self._redis.hset(key, slot, payload)
            self._redis.expire(key, self._ttl)
            return
        self._fallback[session_id][slot] = json.loads(payload)

    def append(self, session_id: str, slot: str, value: Any) -> None:
        existing = self.get(session_id, slot, default=[])
        if not isinstance(existing, list):
            existing = [existing]
        existing.append(value)
        self.set(session_id, slot, existing)

    def all(self, session_id: str) -> Dict[str, Any]:
        if self._redis is not None:
            raw = self._redis.hgetall(self._key(session_id)) or {}
            out: Dict[str, Any] = {}
            for slot, payload in raw.items():
                try:
                    out[slot] = json.loads(payload)
                except json.JSONDecodeError:
                    out[slot] = payload
            return out
        return dict(self._fallback[session_id])

    def clear(self, session_id: str) -> None:
        if self._redis is not None:
            self._redis.delete(self._key(session_id))
        else:
            self._fallback.pop(session_id, None)


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
