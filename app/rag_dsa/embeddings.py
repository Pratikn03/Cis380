from __future__ import annotations

from typing import List

import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer

from app.rag_dsa.config import settings


class DsaEmbeddingModel:
    """Offline-safe embedding model using HashingVectorizer."""

    def __init__(self, dim: int | None = None) -> None:
        self.dim = dim or settings.EMBED_DIM
        self.model = HashingVectorizer(
            n_features=self.dim,
            stop_words="english",
            alternate_sign=False,
            norm="l2",
        )

    def embed(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim))
        matrix = self.model.transform(texts)
        dense = matrix.toarray().astype(float, copy=False)
        if dense.shape[1] != self.dim:
            padded = np.zeros((dense.shape[0], self.dim))
            take = min(self.dim, dense.shape[1])
            padded[:, :take] = dense[:, :take]
            return padded
        return dense
