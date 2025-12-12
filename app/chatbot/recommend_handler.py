"""Combine ML recommender output with LLM explanation."""
from __future__ import annotations

from recommender.inference.recommend import score_single
from recommender.llm_agent.explain_agent import explain_recommendations


def handle_recommendation(user_id: int, movie_id: int, context: str = "") -> str:
    scored = score_single(user_id, movie_id)
    items = [f"movie_id={movie_id}, label={scored['label']}, p={scored.get('probability')}"]
    explained = explain_recommendations(items, user_context=context)
    return explained
