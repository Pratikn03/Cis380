from __future__ import annotations

from typing import Any, Optional

import pandas as pd

from app.models.recommender.features import build_embeddings, catalog_metadata, embed_query_vector
from app.models.recommender.index import RecommenderIndex

_FEATURES_CACHE = None
_INDEX_CACHE = None


def _ensure_resources():
    global _FEATURES_CACHE, _INDEX_CACHE
    if _FEATURES_CACHE is None:
        _FEATURES_CACHE = build_embeddings()
    if _INDEX_CACHE is None:
        meta = catalog_metadata(_FEATURES_CACHE.df)
        _INDEX_CACHE = RecommenderIndex(_FEATURES_CACHE.vectors, meta)
        try:
            _INDEX_CACHE.build()
        except Exception:
            pass
    return _FEATURES_CACHE, _INDEX_CACHE


def recommend(user_id: str = "anon", top_k: int = 5) -> list[dict[str, Any]]:
    import random
    
    features, index = _ensure_resources()
    candidates = []
    for idx, row in features.df.iterrows():
        candidates.append(
            {
                "item_id": row["item_id"],
                "title": row["title"],
                "score": 0.0,
                "source": row["source"],
                "tags": row.get("tags", ""),
            }
        )
    
    # Randomize: pick from larger pool to give varied results
    pool_size = min(50, len(candidates))
    if pool_size > top_k:
        return random.sample(candidates[:pool_size], top_k)
    return candidates[:top_k]


def predict_multimodal(
    *,
    text: Optional[str],
    image_bytes: bytes | None,
    top_k: int = 5,
) -> dict[str, object]:
    text_value = (text or "").strip()
    has_text = bool(text_value)
    has_image = bool(image_bytes)
    if not has_text and not has_image:
        raise ValueError("Provide at least one of text or image.")
    features, index = _ensure_resources()
    query_vec = embed_query_vector(features.vectorizer, text_value if has_text else None, image_bytes)
    hits = index.search(query_vec, top_k=top_k)
    items: list[dict[str, object]] = []
    for idx, score in hits:
        row = features.df.iloc[idx]
        items.append(
            {
                "item_id": row["item_id"],
                "title": row["title"],
                "category": row["category"],
                "brand": row["brand"],
                "price": row["price"],
                "source": row["source"],
                "score": score,
                "image_path": row["image_path"],
                }
            )
    return {
        "mode": "both" if (has_text and has_image) else ("image" if has_image else "text"),
        "items": items,
        "hits": [{"index": idx, "score": score} for idx, score in hits],
        "explanation": f"Similarity search over {features.df.shape[0]} catalog items.",
        "explainability": {
            "used": "both" if (has_text and has_image) else ("image" if has_image else "text"),
            "fusion": "concat(tfidf, semantic512)",
        },
    }


def catalog_dataframe() -> pd.DataFrame:
    features, _ = _ensure_resources()
    return features.df
