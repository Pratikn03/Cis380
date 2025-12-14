from __future__ import annotations

from pathlib import Path
from typing import List

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

try:
    from sentence_transformers import SentenceTransformer

    _HAS_ST = True
except ImportError:
    SentenceTransformer = None  # type: ignore
    _HAS_ST = False


class EmbeddingModel:
    """Wraps a SentenceTransformer embedding model or falls back to TF-IDF."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        if _HAS_ST and SentenceTransformer is not None:
            self.model = SentenceTransformer(model_name)
            self.dim = self.model.get_sentence_embedding_dimension()
            self.use_sentence_transformer = True
        else:
            self.model = TfidfVectorizer(max_features=768)
            self.dim = 768
            self.use_sentence_transformer = False

    def embed(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim))
        if self.use_sentence_transformer and SentenceTransformer is not None:
            embeddings = np.array(self.model.encode(texts, convert_to_numpy=True))
            if embeddings.shape[1] != self.dim:
                self.dim = embeddings.shape[1]
            return embeddings
        matrix = self.model.fit_transform(texts)
        dense = matrix.toarray()
        if dense.shape[1] < self.dim:
            padded = np.zeros((dense.shape[0], self.dim))
            padded[:, : dense.shape[1]] = dense
            return padded
        return dense[:, : self.dim]
