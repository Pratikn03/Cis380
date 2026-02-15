from __future__ import annotations

import logging
import os
from typing import List

import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer

try:
    from sentence_transformers import SentenceTransformer

    _HAS_ST = True
except ImportError:
    SentenceTransformer = None  # type: ignore
    _HAS_ST = False


logger = logging.getLogger(__name__)


class EmbeddingModel:
    """Wraps a SentenceTransformer embedding model with deterministic offline fallback."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        backend = (os.getenv("RAG_EMBED_BACKEND") or "auto").strip().lower()
        if backend not in {"auto", "sentence_transformer", "hashing"}:
            backend = "auto"

        if backend == "hashing":
            self._setup_hashing()
            return

        if _HAS_ST and SentenceTransformer is not None:
            try:
                self.model = SentenceTransformer(model_name)
                self.dim = self.model.get_sentence_embedding_dimension()
                self.use_sentence_transformer = True
                return
            except Exception as exc:  # pragma: no cover - runtime fallback
                # Deterministic fallback is required in offline CI/dev environments.
                logger.warning(
                    "RAG embedding backend fallback to hashing (model=%s, reason=%s)",
                    model_name,
                    exc,
                )
                if backend == "sentence_transformer":
                    raise

        self._setup_hashing()

    def _setup_hashing(self) -> None:
        # Offline-friendly deterministic embeddings without fitting:
        # HashingVectorizer produces a stable fixed-size representation for both
        # docs and queries (unlike fitting TF-IDF per call).
        self.dim = 768
        self.model = HashingVectorizer(
            n_features=self.dim,
            stop_words="english",
            alternate_sign=False,
            norm="l2",
        )
        self.use_sentence_transformer = False

    def embed(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim))
        if self.use_sentence_transformer and SentenceTransformer is not None:
            embeddings = np.array(self.model.encode(texts, convert_to_numpy=True))
            if embeddings.shape[1] != self.dim:
                self.dim = embeddings.shape[1]
            return embeddings
        matrix = self.model.transform(texts)
        dense = matrix.toarray().astype(float, copy=False)
        if dense.shape[1] != self.dim:
            # HashingVectorizer should always match, but keep this defensive.
            padded = np.zeros((dense.shape[0], self.dim))
            take = min(self.dim, dense.shape[1])
            padded[:, :take] = dense[:, :take]
            return padded
        return dense
