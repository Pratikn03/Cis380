"""Movie recommender handler with TMDB optional, fallback static list."""
from __future__ import annotations

from typing import List, Dict

import requests

try:
    from .static_fallbacks import movies_fallback
except ImportError:
    from static_fallbacks import movies_fallback

# Basic genre keyword mapping to TMDB genre IDs (with synonyms)
GENRE_MAP = {
    28: ["action", "action thriller", "superhero", "martial arts"],
    12: ["adventure"],
    16: ["animation", "animated", "kids animation"],
    35: ["comedy", "romcom", "romantic comedy"],
    80: ["crime", "gangster", "detective", "noir"],
    99: ["documentary", "doc"],
    18: ["drama"],
    10751: ["family", "kids", "children"],
    14: ["fantasy", "sword and sorcery"],
    36: ["history", "historical"],
    27: ["horror", "slasher", "scary"],
    10402: ["music", "musical"],
    9648: ["mystery", "whodunit"],
    10749: ["romance", "romantic"],
    878: ["sci-fi", "science fiction", "sci fi", "space"],
    10770: ["tv movie"],
    53: ["thriller", "psychological thriller"],
    10752: ["war", "military"],
    37: ["western"],
}


def _extract_genre_ids(query: str) -> list[int]:
    ids = []
    q = (query or "").lower()
    for gid, keywords in GENRE_MAP.items():
        if any(k in q for k in keywords):
            ids.append(gid)
    return ids


def recommend_movies(query: str, tmdb_api_key: str | None = None, top_n: int = 5) -> List[Dict]:
    """Return a list of movie recommendations."""
    if not tmdb_api_key:
        return movies_fallback(query)

    try:
        params = {
            "api_key": tmdb_api_key,
            "language": "en-US",
            "page": 1,
        }

        q_lower = (query or "").lower()
        genre_ids = _extract_genre_ids(query or "")

        # If user asks for "latest/new/recent" use now_playing sorted by release date
        if any(word in q_lower for word in ["latest", "new", "recent"]):
            url = "https://api.themoviedb.org/3/movie/now_playing"
            params["region"] = "US"
        elif query and any(ch.isalpha() for ch in query):
            params["query"] = query
            url = "https://api.themoviedb.org/3/search/movie"
        else:
            url = "https://api.themoviedb.org/3/movie/popular"

        if genre_ids:
            params["with_genres"] = ",".join(str(g) for g in genre_ids)

        resp = requests.get(url, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])[:top_n]
        out = []
        for r in results:
            year = ""
            if r.get("release_date"):
                year = r.get("release_date", "")[:4]
            out.append(
                {
                    "title": r.get("title") or r.get("name"),
                    "reason": f"Rating: {r.get('vote_average')} · Popularity: {r.get('popularity')} · {year}",
                    "overview": r.get("overview", "")[:200],
                }
            )
        return out or movies_fallback(query)
    except Exception as exc:
        print(f"[movies] TMDB fetch failed: {exc}")
        return movies_fallback(query)


__all__ = ["recommend_movies"]
