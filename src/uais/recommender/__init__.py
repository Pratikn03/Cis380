"""Recommender layer for UAIS-V.

This package provides helpers to turn domain/fusion scores into
actionable recommendations with lightweight explanations.
"""

from .recommend_actions import recommend_from_scores, recommend_from_text
from .rules import assign_action_from_scores

__all__ = ["recommend_from_scores", "recommend_from_text", "assign_action_from_scores"]
