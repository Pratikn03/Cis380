"""Place recommender handler with local catalog + optional API fallback."""

from __future__ import annotations

from typing import List, Dict
import json
import re
from pathlib import Path

import requests

try:
    from .static_fallbacks import places_fallback
except ImportError:
    from static_fallbacks import places_fallback

BASE_DIR = Path(__file__).resolve().parents[3]
PLACES_CATALOG = BASE_DIR / "data" / "catalogs" / "places_catalog.jsonl"


def _load_catalog(path: Path = PLACES_CATALOG) -> List[Dict]:
    if not path.exists():
        return []
    items: List[Dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        title = str(obj.get("title") or "").strip()
        if not title:
            continue
        raw_tags = obj.get("tags") or []
        tag_set = {str(t).lower() for t in raw_tags if str(t).strip()}
        for extra in (
            obj.get("category"),
            obj.get("type"),
            obj.get("best_season"),
            obj.get("vibe"),
            obj.get("city"),
            obj.get("country"),
        ):
            if extra:
                tag_set |= _tokenize(str(extra))
        obj["tags"] = sorted(tag_set)
        items.append(obj)
    return items


def _tokenize(text: str) -> set[str]:
    return {t.lower() for t in re.findall(r"[a-zA-Z0-9]+", text) if len(t) > 2}


def _score_item(item: Dict, tokens: set[str], city: str | None) -> float:
    tags = {str(t).lower() for t in (item.get("tags") or []) if str(t).strip()}
    category = str(item.get("category") or "").lower()
    score = float(len(tokens.intersection(tags)))
    if category and category in tokens:
        score += 0.75
    best_season = str(item.get("best_season") or "").lower()
    if best_season and best_season in tokens:
        score += 0.5
    vibe = str(item.get("vibe") or "").lower()
    if vibe and vibe in tokens:
        score += 0.5
    if city:
        item_city = str(item.get("city") or "").lower()
        if item_city and city.lower() in item_city:
            score += 1.0
    return score


def recommend_places(
    query: str, places_api_key: str | None = None, city: str | None = None, top_n: int = 5
) -> List[Dict]:
    """Return a list of places. Use local catalog when available."""
    local_items = _load_catalog()
    if local_items:
        tokens = _tokenize(query)
        ranked = sorted(
            local_items, key=lambda item: _score_item(item, tokens, city), reverse=True
        )
        picked = ranked[:top_n]
        out = []
        for item in picked:
            title = item.get("title")
            reason = item.get("reason") or ""
            tags = item.get("tags") or []
            location = ", ".join(p for p in [item.get("city"), item.get("country")] if p)
            best_season = item.get("best_season")
            vibe = item.get("vibe")
            if not reason and tags:
                reason = "Tags: " + ", ".join(str(t) for t in tags[:4])
            if best_season:
                reason = f"{reason} · Best season: {best_season}" if reason else f"Best season: {best_season}"
            if vibe:
                reason = f"{reason} · Vibe: {vibe}" if reason else f"Vibe: {vibe}"
            out.append({"title": title, "reason": reason, "location": location})
        return out or places_fallback(query)

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
