from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any, Iterable, Optional

_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "has",
    "have",
    "how",
    "i",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "use",
    "what",
    "when",
    "where",
    "why",
    "with",
}


def stable_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def cache_get(path: str) -> Optional[Any]:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def cache_set(path: str, obj: Any) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(obj, handle, ensure_ascii=True, indent=2)


def tokenize(text: str) -> list[str]:
    tokens = re.split(r"[^a-z0-9_]+", text.lower())
    return [t for t in tokens if t and t not in _STOPWORDS]


def unique_preserve(items: Iterable[str]) -> list[str]:
    seen = set()
    out: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out
