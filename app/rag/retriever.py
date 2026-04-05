from __future__ import annotations

from typing import Dict, List

from app.rag.config import settings
from app.rag.embed import EmbeddingModel
from app.rag.index import RagIndex

_INDEX: RagIndex | None = None


def _get_index() -> RagIndex:
    global _INDEX
    if _INDEX is None:
        _INDEX = RagIndex.load()
    return _INDEX


def _normalize_scores(values: List[float]) -> List[float]:
    if not values:
        return []
    max_val = max(values)
    min_val = min(values)
    if max_val == min_val:
        return [1.0 for _ in values]
    return [(v - min_val) / (max_val - min_val) for v in values]


def merge_hybrid_results(
    dense: List[Dict[str, object]],
    bm25: List[Dict[str, object]],
    *,
    top_k: int,
    alpha: float,
) -> List[Dict[str, object]]:
    dense_scores = _normalize_scores([float(item.get("score", 0.0)) for item in dense])
    bm25_scores = _normalize_scores([float(item.get("score", 0.0)) for item in bm25])

    merged: Dict[str, Dict[str, object]] = {}
    for item, norm_score in zip(dense, dense_scores):
        key = str(item.get("chunk_id") or item.get("source"))
        merged[key] = {**item, "dense_score": norm_score, "hybrid_score": alpha * norm_score}

    for item, norm_score in zip(bm25, bm25_scores):
        key = str(item.get("chunk_id") or item.get("source"))
        if key in merged:
            merged[key]["bm25_score"] = norm_score
            merged[key]["hybrid_score"] = (
                alpha * float(merged[key].get("dense_score", 0.0)) + (1 - alpha) * norm_score
            )
        else:
            merged[key] = {
                **item,
                "bm25_score": norm_score,
                "hybrid_score": (1 - alpha) * norm_score,
            }

    ranked = sorted(merged.values(), key=lambda x: float(x.get("hybrid_score", 0.0)), reverse=True)
    return ranked[:top_k]


def retrieve_context(query: str, top_k: int = 5) -> List[Dict[str, object]]:
    model = EmbeddingModel(model_name=settings.embed_model)
    q_vec = model.embed([query])
    if q_vec.size == 0:
        return []
    index = _get_index()
    dense = index.search_dense(q_vec[0], top_k=settings.topk_dense)
    bm25 = index.search_bm25(query, top_k=settings.topk_bm25)
    return merge_hybrid_results(dense, bm25, top_k=top_k, alpha=settings.hybrid_alpha)
