"""Combine ML recommender output with LLM explanation."""
from __future__ import annotations

from app.models.recommender.explain import explain_recommendation
from app.models.recommender.predict import recommend


def handle_recommendation(user_id: int, movie_id: int, context: str = "") -> str:
    items = recommend(user_id=str(user_id), top_k=1)
    if items:
        item = items[0]
        item_id = item["item_id"]
    else:
        item_id = str(movie_id)
    return explain_recommendation(str(user_id), item_id)
