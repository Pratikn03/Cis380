"""LLM style/personalization stub for recommendations."""

from __future__ import annotations

import os
import requests

OPENAI_KEY = os.getenv("OPENAI_API_KEY")


def style_message(base_text: str, tone: str = "friendly") -> str:
    if not OPENAI_KEY:
        return base_text
    prompt = f"Rewrite the following in a {tone} tone:\n\n{base_text}"
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
    except Exception:
        return base_text
