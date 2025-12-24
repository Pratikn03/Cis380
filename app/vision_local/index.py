from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


try:
    import faiss  # type: ignore

    _HAS_FAISS = True
except Exception:  # pragma: no cover
    faiss = None  # type: ignore
    _HAS_FAISS = False


def _l2_normalize(vecs: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms = np.clip(norms, 1e-8, None)
    return vecs / norms


@dataclass(frozen=True)
class SearchHit:
    index: int
    score: float
    meta: dict[str, Any]


class VectorIndex:
    """Small cosine-similarity index (FAISS if available, numpy fallback)."""

    def __init__(self, vectors: np.ndarray, meta: list[dict[str, Any]]):
        if vectors.ndim != 2:
            raise ValueError("vectors must be 2D")
        if len(meta) != vectors.shape[0]:
            raise ValueError("meta length must match vectors rows")
        self._vectors = _l2_normalize(vectors.astype(np.float32))
        self._meta = meta
        self._faiss = None

    @property
    def dim(self) -> int:
        return int(self._vectors.shape[1])

    def build(self) -> None:
        if _HAS_FAISS:
            idx = faiss.IndexFlatIP(self.dim)  # inner product on normalized vectors
            idx.add(self._vectors)
            self._faiss = idx

    def search(self, query_vec: np.ndarray, top_k: int = 5) -> list[SearchHit]:
        q = query_vec.astype(np.float32)
        norm = np.linalg.norm(q)
        if norm > 0:
            q = q / norm

        if _HAS_FAISS and self._faiss is not None:
            distances, indices = self._faiss.search(q.reshape(1, -1), top_k)
            hits: list[SearchHit] = []
            for score, idx in zip(distances[0].tolist(), indices[0].tolist()):
                if idx < 0:
                    continue
                hits.append(
                    SearchHit(index=int(idx), score=float(score), meta=self._meta[int(idx)])
                )
            return hits

        scores = (q @ self._vectors.T).astype(np.float32)
        order = np.argsort(scores)[::-1][:top_k]
        return [
            SearchHit(index=int(i), score=float(scores[int(i)]), meta=self._meta[int(i)])
            for i in order.tolist()
        ]
