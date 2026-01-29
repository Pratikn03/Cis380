"""Book recommender handler using a local catalog when available."""

from __future__ import annotations

import csv
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

try:
    from .static_fallbacks import books_fallback
except ImportError:  # pragma: no cover
    from static_fallbacks import books_fallback

BASE_DIR = Path(__file__).resolve().parents[3]
BOOKS_CSV = BASE_DIR / "data" / "raw" / "recommendation" / "books.csv"


def _tokenize(text: str) -> set[str]:
    return {t.lower() for t in re.findall(r"[a-zA-Z0-9']+", text) if len(t) > 2}


def _split_tags(value: object) -> set[str]:
    if not value:
        return set()
    tags = set()
    for chunk in str(value).replace("|", ",").split(","):
        chunk = chunk.strip()
        if chunk:
            tags |= _tokenize(chunk)
    return tags


def _parse_float(value: object) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def _parse_int(value: object) -> int:
    try:
        return int(float(value))
    except Exception:
        return 0


@lru_cache(maxsize=1)
def _load_books() -> List[Dict[str, Any]]:
    if not BOOKS_CSV.exists():
        return []
    items: List[Dict[str, Any]] = []
    with BOOKS_CSV.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            title = (row.get("title") or row.get("original_title") or "").strip()
            if not title:
                continue
            authors = (row.get("authors") or "").strip()
            title_tokens = _tokenize(title)
            author_tokens = _tokenize(authors)
            tags = _split_tags(row.get("tags")) | author_tokens | title_tokens
            items.append(
                {
                    "title": title,
                    "authors": authors,
                    "average_rating": _parse_float(row.get("average_rating")),
                    "ratings_count": _parse_int(row.get("ratings_count")),
                    "tags": tags,
                    "_title_tokens": title_tokens,
                    "_author_tokens": author_tokens,
                }
            )
    return items


def _score_item(item: Dict[str, Any], tokens: set[str]) -> float:
    score = float(len(tokens.intersection(item.get("tags", set()))))
    if tokens.intersection(item.get("_author_tokens", set())):
        score += 0.75
    if tokens.intersection(item.get("_title_tokens", set())):
        score += 0.5
    return score


def recommend_books(query: str, top_n: int = 5) -> List[Dict[str, Any]]:
    """Return book recommendations from the local catalog or fallback pool."""
    items = _load_books()
    if not items:
        return books_fallback(query)

    tokens = _tokenize(query or "")
    ranked = sorted(
        items,
        key=lambda item: (
            _score_item(item, tokens),
            item.get("average_rating", 0.0),
            item.get("ratings_count", 0),
        ),
        reverse=True,
    )
    if tokens:
        matches = [item for item in ranked if _score_item(item, tokens) > 0]
        if matches:
            ranked = matches

    out: List[Dict[str, Any]] = []
    for item in ranked[:top_n]:
        reason_bits = []
        authors = item.get("authors") or ""
        if authors:
            reason_bits.append(f"Author: {authors}")
        rating = float(item.get("average_rating") or 0.0)
        if rating:
            reason_bits.append(f"Rating: {rating:.2f}")
        ratings_count = int(item.get("ratings_count") or 0)
        if ratings_count:
            reason_bits.append(f"Ratings: {ratings_count:,}")
        match_tags = sorted(tokens.intersection(item.get("tags", set())))
        if match_tags:
            reason_bits.append(f"Matches: {', '.join(match_tags[:4])}")
        out.append(
            {
                "title": item.get("title"),
                "author": authors,
                "reason": " · ".join(reason_bits) if reason_bits else "Popular reader pick.",
            }
        )
    return out or books_fallback(query)


__all__ = ["recommend_books"]
