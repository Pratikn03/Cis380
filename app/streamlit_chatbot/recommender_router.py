"""Intent routing for the chatbot recommender."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Any, Tuple

# Ensure relative imports work when run via `streamlit run app.py`
THIS_DIR = Path(__file__).resolve().parent
PARENT = THIS_DIR
if str(PARENT) not in sys.path:
    sys.path.append(str(PARENT))

# Try package-relative import first, then fallback to absolute
try:
    from .config import load_config
    from .handlers.movies import recommend_movies
    from .handlers.places import recommend_places
    from .handlers.news import recommend_news
    from .handlers.clothes import recommend_clothes
except ImportError:
    from config import load_config
    from handlers.movies import recommend_movies
    from handlers.places import recommend_places
    from handlers.news import recommend_news
    from handlers.clothes import recommend_clothes


def _detect_intent(text: str) -> Tuple[str, str]:
    """Very simple keyword-based intent detection."""
    t = text.lower()
    if any(k in t for k in ["clothes", "outfit", "fashion", "wear"]):
        return "clothes", text
    if any(k in t for k in ["movie", "film", "show", "latest movies", "new movies"]):
        return "movies", text
    if any(k in t for k in ["place", "restaurant", "cafe", "coffee", "park", "visit", "trip"]):
        return "places", text
    if "health" in t:
        return "news_health", text
    if "crime" in t:
        return "news_crime", text
    if "news" in t or "headline" in t:
        return "news", text
    # default to news/general
    return "news", text


def route_recommendation(text: str) -> Dict[str, Any]:
    """Route the user text to the proper recommender handler."""
    intent, query = _detect_intent(text)
    cfg = load_config()

    # Simple city extractor: looks for "in|near|around|at <City>" or trailing comma-separated city
    city = None
    import re

    m_city = re.search(r"(?:in|near|around|at)\s+([A-Za-z][A-Za-z .'-]+)", query, re.IGNORECASE)
    if not m_city:
        m_city = re.search(r",\s*([A-Za-z][A-Za-z .'-]+)$", query)
    if m_city:
        city = m_city.group(1).strip()

    if intent == "movies":
        items = recommend_movies(query=query, tmdb_api_key=cfg.tmdb_api_key)
        category = "Movies"
    elif intent == "places":
        items = recommend_places(query=query, city=city, places_api_key=cfg.places_api_key)
        category = "Places"
    elif intent == "clothes":
        # Try to extract age from the query
        age = None
        import re

        m = re.search(r"(\d{1,3})", query)
        if m:
            try:
                age = int(m.group(1))
            except Exception:
                age = None
        items = recommend_clothes(age=age, query=query)
        category = "Clothes"
    elif intent == "news_health":
        items = recommend_news(query=query, topic="health", news_api_key=cfg.news_api_key)
        category = "Health News"
    elif intent == "news_crime":
        items = recommend_news(query=query, topic="crime", news_api_key=cfg.news_api_key)
        category = "Crime News"
    else:
        items = recommend_news(query=query, topic=None, news_api_key=cfg.news_api_key)
        category = "News"

    return {
        "category": category,
        "items": items,
    }


__all__ = ["route_recommendation"]
