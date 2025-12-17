from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.vision_local.embedder import clip_available, embed_image_bytes, embed_text


@dataclass(frozen=True)
class DetectedLabel:
    label: str
    score: float


DEFAULT_LABELS: tuple[str, ...] = (
    "phone",
    "laptop",
    "headphones",
    "camera",
    "person",
    "face",
    "document",
    "book",
    "car",
    "food",
)


def _infer_category(labels: list[str]) -> str:
    if any(lbl in labels for lbl in ("phone", "laptop", "headphones", "camera")):
        return "electronics"
    if any(lbl in labels for lbl in ("document", "book")):
        return "documents"
    if any(lbl in labels for lbl in ("person", "face")):
        return "people"
    return "unknown"


def detect_objects(image_bytes: bytes, *, labels: tuple[str, ...] = DEFAULT_LABELS, top_k: int = 3) -> dict[str, object]:
    """Best-effort local object tagging.

    Uses CLIP zero-shot scoring when available locally; otherwise returns empty tags.
    """
    if not labels:
        return {"objects": [], "category": "unknown", "scores": []}

    if not clip_available():
        return {"objects": [], "category": "unknown", "scores": []}

    img_vec = embed_image_bytes(image_bytes)
    text_vecs = np.stack([embed_text(lbl) for lbl in labels], axis=0).astype(np.float32)
    sims = (text_vecs @ img_vec.astype(np.float32)).astype(np.float32)
    order = np.argsort(sims)[::-1][: max(1, int(top_k))]

    detected: list[DetectedLabel] = []
    for idx in order.tolist():
        detected.append(DetectedLabel(label=str(labels[int(idx)]), score=float(sims[int(idx)])))

    objects = [d.label for d in detected]
    category = _infer_category(objects)
    return {
        "objects": objects,
        "category": category,
        "scores": [{"label": d.label, "score": d.score} for d in detected],
    }

