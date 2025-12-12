"""LLM explainer stub for recommendations."""
from __future__ import annotations

import os
import requests

OPENAI_KEY = os.getenv("OPENAI_API_KEY")


def explain_recommendations(items, user_context: str = "") -> str:
    if not OPENAI_KEY:
        return f"LLM key not set. Items: {items}"
    prompt = f"""
    You are a recommendation explainer.
    User context: {user_context}
    Recommended items: {items}
    Write a concise, friendly explanation for why these items fit the user.
    """
    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_KEY}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as exc:  # pragma: no cover
        return f"[LLM error: {exc}] Items: {items}"

