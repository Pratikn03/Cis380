from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import numpy as np

from .catalog import load_default_catalog
from .image_embed import embed_image_bytes, embed_text
from .index_store import IndexPaths, default_index_paths, load_index, search_index
from .types import MultimodalResult


class IndexNotBuiltError(RuntimeError):
    pass


def _l2_normalize(vec: np.ndarray) -> np.ndarray:
    denom = float(np.linalg.norm(vec) + 1e-12)
    return (vec / denom).astype(np.float32)


def multimodal_recommend(
    *,
    image_bytes: bytes | None = None,
    text: str | None = None,
    top_k: int = 5,
    paths: IndexPaths | None = None,
) -> dict[str, object]:
    """Return top_k similar items given image_bytes, text, or both.

    Returns a JSON-serializable dict so API layer can return it directly.
    """

    text_value = (text or "").strip()
    has_text = bool(text_value)
    has_image = bool(image_bytes)
    if not has_text and not has_image:
        raise ValueError("Provide at least one of image_bytes or text")

    paths = paths or default_index_paths()
    index_ready = Path(paths.index_path).exists() and Path(paths.meta_path).exists()

    # Prefer CLIP+FAISS index when available, but fall back to the lightweight
    # catalog vector index so the feature still works without a separate build step.
    if not index_ready:
        from app.models.recommender.predict import predict_multimodal
        from app.vision_local.analyze import analyze_image_bytes

        res = predict_multimodal(text=text_value if has_text else None, image_bytes=image_bytes, top_k=top_k)
        out: dict[str, object] = {"type": "multimodal_recommendation", **res, "backend": "catalog_index"}
        if has_image and image_bytes is not None:
            try:
                out["visual"] = analyze_image_bytes(image_bytes)
            except Exception:
                out["visual"] = {"objects": [], "category": "unknown", "clip_used": False}
        return out

    index, meta = load_index(paths)

    if has_image and has_text and image_bytes is not None:
        img_vec = embed_image_bytes(image_bytes)
        txt_vec = embed_text(text_value)
        query_vec = _l2_normalize(0.5 * img_vec + 0.5 * txt_vec)
        mode = "both"
    elif has_image and image_bytes is not None:
        query_vec = embed_image_bytes(image_bytes)
        mode = "image"
    else:
        query_vec = embed_text(text_value)
        mode = "text"

    hits = search_index(index, meta, query_vec, top_k=top_k)
    # Optional enrichment: if the user has a catalog with image_path fields, map
    # returned hit paths to product-like objects.
    catalog = load_default_catalog()
    items: list[dict[str, object]] = []
    for h in hits:
        # If the hit is a real path, normalize; if it's a synthetic catalog URI,
        # keep it as-is.
        key = h.path if str(h.path).startswith("catalog://") else str(Path(h.path))
        item = None
        if catalog:
            # Normalize to the same form used by catalog keys.
            item_obj = catalog.get(key)
            if item_obj is not None:
                item = item_obj.to_dict()
        if item is None:
            item = {
                "item_id": key,
                "title": Path(h.path).name,
                "category": None,
                "brand": None,
                "price": None,
                "image_path": h.path,
            }
        item["score"] = h.score
        items.append(item)
    result = MultimodalResult(
        mode=mode,
        hits=hits,
        explanation="Recommendations based on CLIP similarity search (image/text).",
    )
    return {
        "type": "multimodal_recommendation",
        "mode": result.mode,
        "hits": [asdict(h) for h in result.hits],
        "items": items,
        "explanation": result.explanation,
        "explainability": {
            "used": mode,
            "fusion": "avg(clip_image, clip_text)" if mode == "both" else None,
            "backend": "clip_faiss_index",
        },
    }
