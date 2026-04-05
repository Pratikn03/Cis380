"""Minimal context manager for storing user preferences."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from time import time
from typing import Dict, Any


@dataclass
class SessionState:
    session_id: str
    created_at: float
    updated_at: float
    last_intent: str | None = None
    last_user_message: str | None = None
    last_domain: str | None = None
    price_preference: float | None = None
    preferred_tags: list[str] | None = None
    turns: int = 0


class ContextManager:
    def __init__(self):
        self._sessions: Dict[str, SessionState] = {}

    def get(self, session_id: str) -> SessionState:
        now = time()
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionState(
                session_id=session_id, created_at=now, updated_at=now
            )
        return self._sessions[session_id]

    def update(self, session_id: str, **fields) -> SessionState:
        state = self.get(session_id)
        for key, value in fields.items():
            if hasattr(state, key):
                setattr(state, key, value)
        state.updated_at = time()
        return state

    def bump_turn(self, session_id: str) -> SessionState:
        state = self.get(session_id)
        state.turns += 1
        state.updated_at = time()
        return state

    def to_dict(self, session_id: str) -> Dict[str, Any]:
        return asdict(self.get(session_id))
