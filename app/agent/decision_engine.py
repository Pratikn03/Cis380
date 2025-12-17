from __future__ import annotations

import re
from typing import Set


class DecisionEngine:
    """Rule-based decision engine for routing requests."""

    FRAUD_KEYWORDS: Set[str] = {"fraud", "scam", "dispute", "transaction", "card", "chargeback"}
    RAG_KEYWORDS: Set[str] = {"docs", "document", "manual", "policy", "according", "according to", "from the file"}
    RECOMMEND_KEYWORDS: Set[str] = {"recommend", "suggest", "similar", "best", "top", "like"}
    RECOMMEND_PHRASES: Set[str] = {"like this", "similar to", "recommendation", "recommendations", "favorite", "favorites"}

    def decide_route(self, text: str, use_rag: bool = True, has_audio: bool = False, has_image: bool = False) -> str:
        normalized = text.lower()
        words = set(re.findall(r"\w+", normalized))

        if has_audio:
            return "voice_emotion"
        if self.FRAUD_KEYWORDS & words:
            return "fraud"
        if use_rag and any(keyword in normalized for keyword in self.RAG_KEYWORDS):
            return "rag"
        if has_image:
            return "recommend"
        if self.RECOMMEND_KEYWORDS & words:
            return "recommend"
        if any(phrase in normalized for phrase in self.RECOMMEND_PHRASES):
            return "recommend"
        return "chat"
