"""Place recommender handler with optional API, fallback static list."""
from __future__ import annotations

from typing import List, Dict

import requests

try:
    from .static_fallbacks import places_fallback
except ImportError:
    from static_fallbacks import places_fallback


def recommend_places(query: str, places_api_key: str | None = None, city: str | None = None, top_n: int = 5) -> List[Dict]:
    """Return a list of places. If no API key, use fallback."""
    if not places_api_key:
        return places_fallback(query)

    try:
        # Simple example using Foursquare Places API if key provided
        url = "https://api.foursquare.com/v3/places/search"
        headers = {"Authorization": places_api_key}
        params = {"query": query or "coffee", "limit": top_n}
        if city:
            params["near"] = city
        resp = requests.get(url, headers=headers, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])[:top_n]
        out = []
        for r in results:
            out.append(
                {
                    "title": r.get("name"),
                    "reason": r.get("categories", [{}])[0].get("name", "Place"),
                    "location": r.get("location", {}).get("formatted_address", ""),
                }
            )
        return out or places_fallback(query)
    except Exception as exc:
        print(f"[places] API fetch failed: {exc}")
        return places_fallback(query)


__all__ = ["recommend_places"]
