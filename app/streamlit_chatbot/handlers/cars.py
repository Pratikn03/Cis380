"""Car recommendation handler with static fallback."""

from __future__ import annotations

from typing import Dict, List

try:
    from .static_fallbacks import cars_fallback
except ImportError:
    from static_fallbacks import cars_fallback


def recommend_cars(query: str) -> List[Dict]:
    """Return a simple list of car suggestions.

    This is a lightweight fallback until a dedicated model or API is wired.
    """
    return cars_fallback(query)


__all__ = ["recommend_cars"]
