from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .types import SearchHit


class OptionalDependencyError(RuntimeError):
    pass


def _require_faiss():
    try:
        import faiss  # type: ignore

        return faiss
    except Exception as exc:  # pragma: no cover
        raise OptionalDependencyError("Multimodal recommender requires 'faiss-cpu'.") from exc


@dataclass(frozen=True)
class IndexPaths:
    index_path: Path
    meta_path: Path


def default_index_paths() -> IndexPaths:
    # Keep consistent with existing project structure.
    root = Path("data/processed/recommendation")
    return IndexPaths(index_path=root / "clip.index", meta_path=root / "clip_meta.json")


def save_index(index, meta: list[dict[str, object]], paths: IndexPaths) -> None:
    paths.index_path.parent.mkdir(parents=True, exist_ok=True)
    faiss = _require_faiss()
    faiss.write_index(index, str(paths.index_path))
    paths.meta_path.write_text(json.dumps(meta, indent=2))


def load_index(paths: IndexPaths | None = None):
    faiss = _require_faiss()
    paths = paths or default_index_paths()
    index = faiss.read_index(str(paths.index_path))
    meta = json.loads(paths.meta_path.read_text())
    return index, meta


def search_index(index, meta: list[dict[str, object]], query_vec: np.ndarray, top_k: int = 5) -> list[SearchHit]:
    vec = np.array([query_vec], dtype=np.float32)
    # Cosine similarity search if vectors are L2-normalized -> inner product
    # We build IndexFlatIP in builder.
    distances, indices = index.search(vec, top_k)
    hits: list[SearchHit] = []
    for score, idx in zip(distances[0].tolist(), indices[0].tolist()):
        if idx < 0 or idx >= len(meta):
            continue
        path = str(meta[idx].get("path", ""))
        hits.append(SearchHit(path=path, score=float(score)))
    return hits
