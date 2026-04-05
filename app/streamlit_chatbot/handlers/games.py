"""Game recommender handler using a local Steam catalog when available."""

from __future__ import annotations

import csv
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

try:
    from .static_fallbacks import games_fallback
except ImportError:  # pragma: no cover
    from static_fallbacks import games_fallback

BASE_DIR = Path(__file__).resolve().parents[3]
GAMES_CSV = BASE_DIR / "data" / "raw" / "recommendation" / "games.csv"


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
def _load_games() -> List[Dict[str, Any]]:
    if not GAMES_CSV.exists():
        return []
    items: List[Dict[str, Any]] = []
    with GAMES_CSV.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            title = (row.get("title") or row.get("name") or "").strip()
            if not title:
                continue
            title_tokens = _tokenize(title)
            tags = _split_tags(row.get("tags")) | title_tokens
            items.append(
                {
                    "title": title,
                    "tags": tags,
                    "rating_label": (row.get("rating") or "").strip(),
                    "positive_ratio": _parse_float(row.get("positive_ratio")),
                    "user_reviews": _parse_int(row.get("user_reviews")),
                    "price_final": _parse_float(row.get("price_final")),
                    "_title_tokens": title_tokens,
                }
            )
    return items


def _score_item(item: Dict[str, Any], tokens: set[str]) -> float:
    score = float(len(tokens.intersection(item.get("tags", set()))))
    if tokens.intersection(item.get("_title_tokens", set())):
        score += 0.5
    return score


def recommend_games(query: str, top_n: int = 5) -> List[Dict[str, Any]]:
    """Return game recommendations from the local catalog or fallback pool."""
    items = _load_games()
    if not items:
        return games_fallback(query)

    tokens = _tokenize(query or "")
    ranked = sorted(
        items,
        key=lambda item: (
            _score_item(item, tokens),
            item.get("positive_ratio", 0.0),
            item.get("user_reviews", 0),
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
        rating_label = item.get("rating_label") or ""
        if rating_label:
            reason_bits.append(f"Rating: {rating_label}")
        positive_ratio = float(item.get("positive_ratio") or 0.0)
        if positive_ratio:
            reason_bits.append(f"Positive: {positive_ratio:.0f}%")
        user_reviews = int(item.get("user_reviews") or 0)
        if user_reviews:
            reason_bits.append(f"Reviews: {user_reviews:,}")
        price_final = float(item.get("price_final") or 0.0)
        if price_final:
            reason_bits.append(f"Price: ${price_final:.2f}")
        match_tags = sorted(tokens.intersection(item.get("tags", set())))
        if match_tags:
            reason_bits.append(f"Matches: {', '.join(match_tags[:4])}")
        out.append(
            {
                "title": item.get("title"),
                "reason": " · ".join(reason_bits) if reason_bits else "Trending on Steam.",
            }
        )
    return out or games_fallback(query)


__all__ = ["recommend_games"]
