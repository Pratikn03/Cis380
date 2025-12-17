"""Movie recommender handler with TMDB optional, fallback static list."""
from __future__ import annotations

import csv
import re
from functools import lru_cache
from pathlib import Path
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

_TMDB_TO_MOVIELENS = {
    28: "Action",
    12: "Adventure",
    16: "Animation",
    35: "Comedy",
    80: "Crime",
    99: "Documentary",
    18: "Drama",
    10751: "Children",
    14: "Fantasy",
    36: "History",
    27: "Horror",
    10402: "Musical",
    9648: "Mystery",
    10749: "Romance",
    878: "Sci-Fi",
    10770: "TV Movie",
    53: "Thriller",
    10752: "War",
    37: "Western",
}

BASE_DIR = Path(__file__).resolve().parents[3]
ITEMS_CSV = BASE_DIR / "data" / "raw" / "recommendation" / "items.csv"

_STOPWORDS = {
    "recommend",
    "recommends",
    "movie",
    "movies",
    "film",
    "films",
    "show",
    "shows",
    "latest",
    "new",
    "top",
    "best",
    "good",
    "great",
    "watch",
    "to",
    "for",
    "a",
    "an",
    "the",
    "me",
}


def _extract_genre_ids(query: str) -> list[int]:
    ids = []
    q = (query or "").lower()
    for gid, keywords in GENRE_MAP.items():
        if any(k in q for k in keywords):
            ids.append(gid)
    return ids


@lru_cache(maxsize=1)
def _load_movielens_items() -> list[dict]:
    if not ITEMS_CSV.exists():
        return []
    items: list[dict] = []
    with ITEMS_CSV.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            title = (row.get("title") or "").strip()
            tags = (row.get("tags") or "").strip()
            popularity = row.get("popularity") or "0"
            try:
                pop_val = int(float(popularity))
            except Exception:
                pop_val = 0
            if not title:
                continue
            items.append({"title": title, "tags": tags, "popularity": pop_val})
    return items


def _extract_movielens_genres(query: str) -> list[str]:
    genre_ids = _extract_genre_ids(query or "")
    genres = []
    for gid in genre_ids:
        mapped = _TMDB_TO_MOVIELENS.get(gid)
        if mapped and mapped not in genres:
            genres.append(mapped)
    return genres


def _extract_title_terms(query: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", (query or "").lower())
    terms = [t for t in tokens if len(t) > 2 and t not in _STOPWORDS]
    # Keep only a few terms to avoid over-filtering.
    return terms[:4]


def _recommend_movies_offline(query: str, top_n: int) -> list[dict]:
    items = _load_movielens_items()
    if not items:
        return movies_fallback(query)

    genres = _extract_movielens_genres(query)
    terms = _extract_title_terms(query)

    filtered = items
    if genres:
        filtered = [
            it
            for it in filtered
            if it.get("tags") and all(g.lower() in it["tags"].lower().split("|") for g in genres)
        ]
    if terms and not genres:
        filtered = [it for it in filtered if any(term in it["title"].lower() for term in terms)]

    if not filtered:
        filtered = items

    if genres:
        def _focus(it: dict) -> float:
            tag_str = it.get("tags") or ""
            parts = [p for p in tag_str.split("|") if p]
            if not parts:
                return 0.0
            return len(genres) / len(parts)

        def _focused_popularity(it: dict) -> float:
            pop = float(it.get("popularity") or 0)
            focus = _focus(it)
            return pop * (focus**2)

        filtered.sort(
            key=lambda it: (_focused_popularity(it), int(it.get("popularity") or 0)),
            reverse=True,
        )
    else:
        filtered.sort(key=lambda it: int(it.get("popularity") or 0), reverse=True)

    out: list[dict] = []
    for it in filtered[:top_n]:
        tags = it.get("tags") or ""
        pop = int(it.get("popularity") or 0)
        reason_parts = []
        if tags:
            reason_parts.append(f"Genres: {tags.replace('|', ', ')}")
        if pop:
            reason_parts.append(f"Popularity: {pop}")
        out.append(
            {
                "title": it.get("title"),
                "reason": " · ".join(reason_parts) if reason_parts else "MovieLens recommendation",
            }
        )
    return out or movies_fallback(query)


def recommend_movies(query: str, tmdb_api_key: str | None = None, top_n: int = 5) -> List[Dict]:
    """Return a list of movie recommendations."""
    if not tmdb_api_key:
        return _recommend_movies_offline(query, top_n=top_n)

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
