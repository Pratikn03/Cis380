"""Public API for recommendations."""
from __future__ import annotations

from typing import Dict, Any

from .recommender_engine import recommend_from_scores, recommend_from_text

__all__ = ["recommend_from_scores", "recommend_from_text"]
