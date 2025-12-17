from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SearchHit:
    path: str
    score: float


@dataclass(frozen=True)
class MultimodalResult:
    mode: str  # "image" | "text"
    hits: list[SearchHit]
    explanation: str
