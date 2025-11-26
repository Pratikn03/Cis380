"""News/Health/Crime recommender handler with optional API, fallback static list."""
from __future__ import annotations

from typing import List, Dict

import requests

try:
    from .static_fallbacks import news_fallback
except ImportError:
    from static_fallbacks import news_fallback


def recommend_news(query: str, topic: str | None = None, news_api_key: str | None = None, top_n: int = 5) -> List[Dict]:
    """Return a list of news items. Topic can be 'health' or 'crime' etc."""
    topic = topic or query or "general"
    q_lower = (query or "").lower()
    if not news_api_key:
        return news_fallback(query, topic=topic)

    try:
        url = "https://newsapi.org/v2/top-headlines"
        params = {"apiKey": news_api_key, "pageSize": top_n, "language": "en"}
        # If "latest" in query, bias to latest by not setting q (API already returns top headlines)
        if "latest" in q_lower or "recent" in q_lower:
            params["q"] = topic if topic else None
        else:
            if topic.lower() in {"business", "entertainment", "health", "science", "sports", "technology"}:
                params["category"] = topic.lower()
            else:
                params["q"] = topic
        resp = requests.get(url, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("articles", [])[:top_n]
        out = []
        for r in results:
            out.append(
                {
                    "title": r.get("title"),
                    "reason": r.get("description", "")[:200],
                    "url": r.get("url"),
                }
            )
        return out or news_fallback(query, topic=topic)
    except Exception as exc:
        print(f"[news] API fetch failed: {exc}")
        return news_fallback(query, topic=topic)


__all__ = ["recommend_news"]
