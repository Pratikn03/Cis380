from __future__ import annotations

from pathlib import Path
from typing import List, Dict

import numpy as np

from app.rag.vector_store import VectorStore
from app.rag.embed import EmbeddingModel

ROOT = Path(__file__).resolve().parents[1]
EMBED_DIR = ROOT.parent / "data" / "embeddings"

_VECTOR_STORE: VectorStore | None = None


def _get_store() -> VectorStore:
    global _VECTOR_STORE
    if _VECTOR_STORE is None:
        _VECTOR_STORE = VectorStore(EMBED_DIR)
    return _VECTOR_STORE


def retrieve_context(query: str, top_k: int = 5) -> List[Dict[str, object]]:
    model = EmbeddingModel()
    q_vec = model.embed([query])
    if q_vec.size == 0:
        return []
    store = _get_store()
    return store.search(q_vec[0], top_k=top_k)
