"""Simple saliency for sequence models (heuristic)."""
from typing import Dict

import numpy as np


def sequence_saliency(sequences: np.ndarray, mask: np.ndarray) -> Dict[int, float]:
    """Compute a basic per-time-step saliency using feature magnitudes.

    This is a heuristic placeholder until attention/gradient-based methods are added.
    """
    masked = sequences * mask[:, :, None]
    step_scores = masked.mean(axis=2).mean(axis=0)
    return {int(i): float(score) for i, score in enumerate(step_scores)}


__all__ = ["sequence_saliency"]
