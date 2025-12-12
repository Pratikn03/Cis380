from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np

from .embed import EmbeddedCorpus


def _cosine_similarity(matrix: np.ndarray, vector: np.ndarray) -> np.ndarray:
    if matrix.size == 0 or vector.size == 0:
        return np.array([])
    dot = matrix @ vector
    norm_matrix = np.linalg.norm(matrix, axis=1)
    norm_vector = np.linalg.norm(vector)
    denom = norm_matrix * norm_vector
    denom[denom == 0] = 1.0
    return dot / denom


def retrieve(query: str, corpus: EmbeddedCorpus, top_k: int = 5) -> list[dict]:
    """Return the top matching documents for `query`."""
    if not corpus.docs:
        return []
    q_vec = corpus.vectorizer.transform([query]).toarray().ravel()
    sims = _cosine_similarity(corpus.matrix, q_vec)
    if sims.size == 0:
        return []
    idx = np.argsort(sims)[::-1][:top_k]
    results = []
    for i in idx:
        score = float(sims[i])
        if score <= 0:
            continue
        results.append(
            {"id": corpus.docs[i]["id"], "path": corpus.docs[i]["path"], "text": corpus.docs[i]["text"], "score": score}
        )
    return results
