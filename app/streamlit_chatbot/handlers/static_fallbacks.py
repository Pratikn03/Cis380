"""Static fallback recommendations when APIs are unavailable."""
from __future__ import annotations

from typing import List, Dict


def movies_fallback(query: str) -> List[Dict]:
    return [
        {"title": "Inception", "reason": "Mind-bending sci-fi heist; genre: action/sci-fi"},
        {"title": "The Dark Knight", "reason": "Top-rated superhero thriller; genre: action/crime"},
        {"title": "Interstellar", "reason": "Epic space drama; genre: sci-fi/drama"},
    ]


def places_fallback(query: str) -> List[Dict]:
    return [
        {"title": "Local Coffee House", "reason": "Well-rated cafe nearby"},
        {"title": "Central Park", "reason": "Popular outdoor spot to relax"},
        {"title": "City Museum", "reason": "Top cultural attraction"},
    ]


def news_fallback(query: str, topic: str | None = None) -> List[Dict]:
    return [
        {"title": "Global markets update", "reason": "Top headline; finance"},
        {"title": "Healthcare innovation roundup", "reason": "Top headline; health"},
        {"title": "Technology trends this week", "reason": "Top headline; tech"},
    ]


__all__ = ["movies_fallback", "places_fallback", "news_fallback"]
