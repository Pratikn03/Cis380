from __future__ import annotations

from pathlib import Path
from typing import Any

from app.vision_local.detector import detect_objects
from app.vision_local.embedder import clip_available, embed_image_bytes


def analyze_image_bytes(image_bytes: bytes) -> dict[str, Any]:
    """Analyze an image and return structured visual context."""
    det = detect_objects(image_bytes)
    emb = embed_image_bytes(image_bytes)
    return {
        "objects": det.get("objects", []),
        "category": det.get("category", "unknown"),
        "scores": det.get("scores", []),
        "clip_used": bool(clip_available()),
        "image_embedding": emb.astype(float).tolist(),
    }


def analyze_image(image_path: str | Path) -> dict[str, Any]:
    """Analyze an image from disk.

    Returns:
        {"objects": [...], "category": "...", "image_embedding": [...]}
    """
    path = Path(image_path)
    return analyze_image_bytes(path.read_bytes())

