from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np


try:
    import faiss  # type: ignore

    _HAS_FAISS = True
except ImportError:  # pragma: no cover
    faiss = None  # type: ignore
    _HAS_FAISS = False


@dataclass(frozen=True)
class IndexPaths:
    index_path: Path
    vectors_path: Path
    meta_path: Path


def default_index_paths(base: Path | None = None) -> IndexPaths:
    base = base or Path("data/embeddings")
    base.mkdir(parents=True, exist_ok=True)
    return IndexPaths(
        index_path=base / "recommender.index",
        vectors_path=base / "recommender_vectors.npy",
        meta_path=base / "recommender_meta.json",
    )


def _l2_normalize(vecs: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms = np.clip(norms, 1e-8, None)
    return vecs / norms


class RecommenderIndex:
    def __init__(self, vectors: np.ndarray, meta: list[dict[str, object]], paths: IndexPaths | None = None):
        if vectors.ndim != 2:
            raise ValueError("vectors must be 2D")
        self.paths = paths or default_index_paths()
        self._vectors = _l2_normalize(vectors.astype(np.float32))
        self.meta = meta
        self._faiss_index = None

    @property
    def dim(self) -> int:
        return self._vectors.shape[1]

    def build(self) -> None:
        if _HAS_FAISS:
            index = faiss.IndexFlatIP(self.dim)  # inner product on normalized vectors
            index.add(self._vectors)
            faiss.write_index(index, str(self.paths.index_path))
            self._faiss_index = index
        np.save(self.paths.vectors_path, self._vectors)
        self.paths.meta_path.write_text(json.dumps(self.meta, indent=2))

    def search(self, query_vec: np.ndarray, top_k: int = 5) -> list[tuple[int, float]]:
        query = query_vec.astype(np.float32)
        norm = np.linalg.norm(query)
        if norm > 0:
            query = query / norm
        if _HAS_FAISS and self.paths.index_path.exists():
            if self._faiss_index is None:
                self._faiss_index = faiss.read_index(str(self.paths.index_path))
            distances, indices = self._faiss_index.search(query.reshape(1, -1), top_k)
            return [
                (int(idx), float(score))
                for score, idx in zip(distances[0].tolist(), indices[0].tolist())
                if idx >= 0
            ]
        if self._vectors.size == 0:
            return []
        scores = (query @ self._vectors.T).astype(np.float32)
        idxs = np.argsort(scores)[::-1][:top_k]
        return [(int(idx), float(scores[int(idx)])) for idx in idxs]

    @classmethod
    def load_from_disk(cls, paths: IndexPaths | None = None) -> RecommenderIndex:
        paths = paths or default_index_paths()
        if not paths.vectors_path.exists() or not paths.meta_path.exists():
            raise FileNotFoundError("Recommender index or metadata missing.")
        vectors = np.load(paths.vectors_path)
        meta = json.loads(paths.meta_path.read_text())
        return cls(vectors=vectors, meta=meta, paths=paths)

    def save_meta(self, rows: Iterable[dict[str, object]]) -> None:
        self.paths.meta_path.write_text(json.dumps(list(rows), indent=2))
