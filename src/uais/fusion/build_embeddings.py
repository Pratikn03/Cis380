"""Utilities for building/combining embeddings across domains."""
from typing import Dict, Iterable

import numpy as np
from sklearn.preprocessing import StandardScaler


def to_embedding(matrix: np.ndarray) -> np.ndarray:
    """Scale a numeric matrix to be used as an embedding."""
    scaler = StandardScaler()
    return scaler.fit_transform(matrix)


def merge_embeddings(embeddings: Dict[str, np.ndarray]) -> np.ndarray:
    """Horizontally concatenate embeddings from multiple domains.

    All embeddings are trimmed to the shortest length to keep alignment simple.
    """
    if not embeddings:
        return np.array([])
    min_len = min(arr.shape[0] for arr in embeddings.values())
    trimmed = [arr[:min_len] for arr in embeddings.values()]
    return np.concatenate(trimmed, axis=1)


def generate_meta_features(score_dict: Dict[str, Iterable[float]]) -> np.ndarray:
    """Convert domain -> score iterable into a 2D meta-feature array."""
    keys = sorted(score_dict)
    stacked = np.column_stack([np.array(list(score_dict[k])) for k in keys])
    return stacked


__all__ = ["to_embedding", "merge_embeddings", "generate_meta_features"]
