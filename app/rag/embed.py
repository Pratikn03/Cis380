from __future__ import annotations

import logging
import os
import re
from typing import List

import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """Wraps a SentenceTransformer embedding model with deterministic offline fallback."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        backend = (os.getenv("RAG_EMBED_BACKEND") or "hashing").strip().lower()
        if backend not in {"auto", "sentence_transformer", "hashing"}:
            backend = "auto"

        if backend == "hashing":
            self._setup_hashing()
            return

        SentenceTransformer = None  # type: ignore[assignment]
        has_st = False
        try:
            from sentence_transformers import SentenceTransformer as _SentenceTransformer

            SentenceTransformer = _SentenceTransformer  # type: ignore[assignment]
            has_st = True
        except Exception:
            has_st = False

        if has_st and SentenceTransformer is not None:
            try:
                self.model = SentenceTransformer(model_name)
                self.dim = self.model.get_sentence_embedding_dimension()
                self.use_sentence_transformer = True
                self._sentence_transformer_available = True
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

        self._sentence_transformer_available = False
        self._setup_hashing()

    def _setup_hashing(self) -> None:
        # Offline-friendly deterministic embeddings without fitting:
        # Use lightweight token hashing to avoid heavyweight sklearn imports.
        self.dim = 768
        self.model = None
        self.use_sentence_transformer = False

    def _hashing_embed(self, texts: List[str]) -> np.ndarray:
        vectors = np.zeros((len(texts), self.dim), dtype=float)
        for row, text in enumerate(texts):
            tokens = re.findall(r"[A-Za-z0-9_]+", (text or "").lower())
            if not tokens:
                continue
            for token in tokens:
                idx = hash(token) % self.dim
                vectors[row, idx] += 1.0
            norm = np.linalg.norm(vectors[row])
            if norm > 0:
                vectors[row] /= norm
        return vectors

    def embed(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim))
        if self.use_sentence_transformer and getattr(self, "_sentence_transformer_available", False):
            embeddings = np.array(self.model.encode(texts, convert_to_numpy=True))
            if embeddings.shape[1] != self.dim:
                self.dim = embeddings.shape[1]
            return embeddings
        return self._hashing_embed(texts)
