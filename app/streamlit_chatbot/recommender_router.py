"""Intent routing for the chatbot recommender."""

from __future__ import annotations

import re
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
    from .handlers.movies import recommend_movies, is_movie_similarity_query
    from .handlers.places import recommend_places
    from .handlers.news import recommend_news
    from .handlers.clothes import recommend_clothes
    from .handlers.electronics import recommend_electronics
    from .handlers.cars import recommend_cars
    from .handlers.courses import recommend_courses
except ImportError:
    from config import load_config
    from handlers.movies import recommend_movies, is_movie_similarity_query
    from handlers.places import recommend_places
    from handlers.news import recommend_news
    from handlers.clothes import recommend_clothes
    from handlers.electronics import recommend_electronics
    from handlers.cars import recommend_cars
    from handlers.courses import recommend_courses


def _detect_intent(text: str) -> Tuple[str, str]:
    """Very simple keyword-based intent detection."""
    t = text.lower()
    tokens = set(re.findall(r"[a-z0-9]+", t))

    if tokens.intersection({"clothes", "outfit", "outfits", "clothing", "fashion", "wear", "apparel"}):
        return "clothes", text

    phone_terms = {
        "phone",
        "phones",
        "cellphone",
        "smartphone",
        "smartphones",
        "iphone",
        "pixel",
        "galaxy",
        "android",
    }
    laptop_terms = {
        "laptop",
        "laptops",
        "notebook",
        "notebooks",
        "macbook",
        "thinkpad",
        "xps",
        "dell",
        "lenovo",
        "hp",
        "asus",
        "acer",
        "surface",
    }
    headphone_terms = {
        "headphone",
        "headphones",
        "earbud",
        "earbuds",
        "earphone",
        "headset",
        "airpods",
        "bose",
        "sony",
    }

    if tokens.intersection(phone_terms | laptop_terms | headphone_terms):
        if tokens.intersection(laptop_terms):
            return "laptops", text
        if tokens.intersection(phone_terms):
            return "phones", text
        return "headphones", text

    car_terms = {
        "car",
        "cars",
        "vehicle",
        "vehicles",
        "suv",
        "sedan",
        "hatchback",
        "truck",
        "pickup",
        "ev",
        "electric",
        "hybrid",
        "tesla",
        "bmw",
        "audi",
        "toyota",
        "honda",
    }
    if tokens.intersection(car_terms):
        return "cars", text

    # "Recommend something like Titanic" (no explicit 'movie' token) should still route to movies,
    # but only if the query isn't clearly about electronics/courses/etc.
    try:
        if is_movie_similarity_query(text):
            return "movies", text
    except Exception:
        pass
    if tokens.intersection({"course", "learn", "skill", "training", "certification"}):
        return "courses", text

    movie_terms = {
        "movie",
        "movies",
        "film",
        "films",
        "show",
        "shows",
        "latest movies",
        "new movies",
        # genre keywords so users can type just "romantic", "sci-fi", etc.
        "romance",
        "romantic",
        "romcom",
        "action",
        "comedy",
        "drama",
        "thriller",
        "horror",
        "mystery",
        "crime",
        "sci-fi",
        "scifi",
        "science fiction",
        "fantasy",
        "animation",
        "documentary",
    }
    if tokens.intersection(movie_terms) or "science fiction" in t:
        return "movies", text
    if tokens.intersection(
        {
            "place",
            "restaurant",
            "cafe",
            "coffee",
            "park",
            "visit",
            "trip",
            "hotel",
            "resort",
            "beach",
            "museum",
            "bar",
        }
    ):
        return "places", text
    if "health" in t:
        return "news_health", text
    if "crime" in t:
        return "news_crime", text
    if "news" in t or "headline" in t:
        return "news", text
    # default to news/general
    return "news", text


def _extract_price(query: str) -> float | None:
    import re

    m = re.search(r"under\s*\$?(\d+)", query.lower())
    if m:
        return float(m.group(1))
    m2 = re.search(r"\$(\d+)", query.lower())
    if m2:
        return float(m2.group(1))
    return None


def _extract_tags(query: str) -> set[str]:
    tokens = re.findall(r"[a-zA-Z0-9]+", query.lower())
    return {t for t in tokens if len(t) > 2}


def route_recommendation(text: str, preference: dict | None = None) -> Dict[str, Any]:
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

    price_pref = preference.get("price") if preference else None
    tag_pref = preference.get("preferred_tags", set()) if preference else set()

    if intent == "movies":
        items = recommend_movies(query=query, tmdb_api_key=cfg.tmdb_api_key)
        category = "Movies"
    elif intent == "places":
        items = recommend_places(query=query, city=city, places_api_key=cfg.places_api_key)
        category = "Places"
    elif intent in {"phones", "laptops", "headphones"}:
        items = recommend_electronics(
            domain=intent, query=query, price_limit=price_pref, preferred_tags=tag_pref
        )
        category = intent.capitalize()
    elif intent == "courses":
        items = recommend_courses(query=query)
        category = "Courses"
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
        items = recommend_clothes(
            age=age,
            query=query,
            preferred_tags=sorted([str(t) for t in (tag_pref or set())]),
        )
        category = "Clothes"
    elif intent == "cars":
        items = recommend_cars(query=query)
        category = "Cars"
    elif intent == "news_health":
        items = recommend_news(query=query, topic="health", news_api_key=cfg.news_api_key)
        category = "Health News"
    elif intent == "news_crime":
        items = recommend_news(query=query, topic="crime", news_api_key=cfg.news_api_key)
        category = "Crime News"
    else:
        items = recommend_news(query=query, topic=None, news_api_key=cfg.news_api_key)
        category = "News"

    # Generate varied answer text
    import random
    intros = [
        f"Here are some {category.lower()} picks:",
        f"I found these great {category.lower()} for you:",
        f"Check out these {category.lower()} recommendations:",
        f"Based on your request, here are some {category.lower()}:",
        f"You might enjoy these {category.lower()}:",
    ]
    
    answer_lines = [random.choice(intros)]
    for i, item in enumerate(items[:5], 1):
        title = item.get("title", "Unknown")
        reason = item.get("reason", "")
        if reason:
            answer_lines.append(f"{i}. {title} — {reason}")
        else:
            answer_lines.append(f"{i}. {title}")
    
    answer = "\n".join(answer_lines)

    return {
        "route": "recommend",
        "answer": answer,
        "reply": answer,
        "category": category,
        "items": items,
        "intent": intent,
        "available": True,
    }


__all__ = ["route_recommendation"]
