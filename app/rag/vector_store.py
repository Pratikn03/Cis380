from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import json
import numpy as np

try:
    import faiss

    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False


class VectorStore:
    def __init__(self, persist_dir: Path):
        self.persist_dir = persist_dir
        self.embeddings_path = persist_dir / "embeddings.npy"
        self.metadata_path = persist_dir / "metadata.json"
        self.faiss_path = persist_dir / "faiss.index"
        self.metadata: List[Dict[str, object]] = []
        self.embeddings: np.ndarray = np.zeros((0, 0))
        self._index = None
        self.dim: Optional[int] = None
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self) -> None:
        if self.metadata_path.exists():
            payload = json.loads(self.metadata_path.read_text(encoding="utf-8"))
            self.metadata = payload.get("entries", [])
            self.dim = payload.get("dim")
        if self.embeddings_path.exists():
            self.embeddings = np.load(self.embeddings_path)
            self.dim = self.dim or self.embeddings.shape[1]
            self._build_index()

    def set_embeddings(self, metadata: List[Dict[str, object]], embeddings: np.ndarray) -> None:
        self.metadata = metadata
        self.embeddings = embeddings
        if not embeddings.size:
            self.dim = self.dim or 0
        else:
            self.dim = embeddings.shape[1]
        self._build_index()
        self._persist()

    def _build_index(self) -> None:
        if not self.embeddings.size:
            self._index = None
            return
        if HAS_FAISS:
            matrix = self._normalize(self.embeddings)
            index = faiss.IndexFlatIP(matrix.shape[1])
            index.add(matrix)
            self._index = index
        else:
            self._index = None

    def _persist(self) -> None:
        np.save(self.embeddings_path, self.embeddings)
        payload = {"dim": self.dim, "entries": self.metadata}
        self.metadata_path.write_text(json.dumps(payload), encoding="utf-8")
        if HAS_FAISS and self._index and self.faiss_path:
            faiss.write_index(self._index, str(self.faiss_path))

    def search(self, query_vec: np.ndarray, top_k: int = 5) -> List[Dict[str, object]]:
        if not self.embeddings.size:
            return []
        if self._index is not None:
            normalized = self._normalize(query_vec.reshape(1, -1))
            scores, idxs = self._index.search(normalized, min(top_k, len(self.metadata)))
            idxs = idxs.flatten()
            scores = scores.flatten()
        else:
            normed_embeddings = self._normalize(self.embeddings)
            query_norm = self._normalize(query_vec.reshape(1, -1)).flatten()
            scores = normed_embeddings @ query_norm
            idxs = np.argsort(scores)[::-1][: min(top_k, len(scores))]
            scores = scores[idxs]
        results = []
        for idx, score in zip(idxs, scores):
            if idx >= len(self.metadata):
                continue
            meta = self.metadata[idx]
            result = {
                "source": meta.get("source"),
                "text": meta.get("text"),
                "score": float(score),
                "chunk_id": meta.get("chunk_id"),
            }
            if "doc_id" in meta:
                result["doc_id"] = meta.get("doc_id")
            if "topic" in meta:
                result["topic"] = meta.get("topic")
            results.append(result)
        return results

    def _normalize(self, matrix: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return matrix / norms
