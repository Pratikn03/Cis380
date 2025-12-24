"""Simple ranker for candidate scores."""

from __future__ import annotations

import numpy as np


def rank_candidates(scores: np.ndarray, top_k: int = 5):
    idx = np.argsort(scores)[::-1][:top_k]
    return idx
