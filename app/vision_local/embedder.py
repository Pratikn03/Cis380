from __future__ import annotations

import os
import functools
import hashlib
import io
from typing import Any

import numpy as np


class OptionalDependencyError(RuntimeError):
    """Raised when an optional embedding backend isn't available locally."""


def _l2_normalize(vec: np.ndarray) -> np.ndarray:
    vec = vec.astype(np.float32, copy=False)
    denom = float(np.linalg.norm(vec) + 1e-12)
    return (vec / denom).astype(np.float32)


def _fallback_text_embedding(text: str, *, dim: int = 512) -> np.ndarray:
    counts = np.zeros((dim,), dtype=np.float32)
    for raw in (text or "").lower().split():
        token = raw.strip()
        if not token:
            continue
        digest = hashlib.md5(token.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:4], "little") % dim
        counts[idx] += 1.0
    return _l2_normalize(counts)


def _fallback_image_embedding(image_bytes: bytes, *, bins: int = 8) -> np.ndarray:
    try:
        from PIL import Image
    except Exception as exc:  # pragma: no cover
        raise OptionalDependencyError("Image fallback embedding requires 'pillow'.") from exc

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    arr = np.asarray(img, dtype=np.uint8)
    if arr.ndim != 3 or arr.shape[2] != 3:
        return _l2_normalize(np.zeros((bins**3,), dtype=np.float32))

    # 8 bins per channel => 512-d histogram (bins^3)
    step = 256 // bins
    r = (arr[..., 0] // step).astype(np.int32)
    g = (arr[..., 1] // step).astype(np.int32)
    b = (arr[..., 2] // step).astype(np.int32)
    idx = (r * (bins * bins) + g * bins + b).ravel()
    hist = np.bincount(idx, minlength=bins**3).astype(np.float32)
    return _l2_normalize(hist)


def _embedding_backend() -> str:
    return os.getenv("UAIS_EMBEDDINGS_BACKEND", "auto").strip().lower()


@functools.lru_cache(maxsize=1)
def _load_clip() -> tuple[Any, Any, str]:
    """Load CLIP lazily.

    Important: uses `local_files_only=True` so it never downloads weights.
    """
    try:
        import torch
        from transformers import CLIPModel, CLIPProcessor
    except Exception as exc:  # pragma: no cover
        raise OptionalDependencyError(
            "CLIP embedding requires 'torch' and 'transformers'."
        ) from exc

    device = "cuda"
    if not torch.cuda.is_available():
        device = (
            "mps"
            if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available()
            else "cpu"
        )
    try:
        model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32", local_files_only=True).to(
            device
        )
        processor = CLIPProcessor.from_pretrained(
            "openai/clip-vit-base-patch32", local_files_only=True
        )
    except Exception as exc:
        raise OptionalDependencyError(
            "CLIP weights not available locally. Run once online to cache, or use fallback embeddings."
        ) from exc

    model.eval()
    return model, processor, device


def clip_available() -> bool:
    if _embedding_backend() == "fallback":
        return False
    try:
        _load_clip()
        return True
    except OptionalDependencyError:
        return False


def embed_text(text: str) -> np.ndarray:
    if _embedding_backend() == "fallback":
        return _fallback_text_embedding(text)
    try:
        model, processor, device = _load_clip()
        import torch

        inputs = processor(text=[text], return_tensors="pt", padding=True)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            features = model.get_text_features(**inputs)
        vec = features.detach().cpu().numpy()[0]
        return _l2_normalize(vec)
    except OptionalDependencyError:
        return _fallback_text_embedding(text)


def embed_image_bytes(image_bytes: bytes) -> np.ndarray:
    try:
        from PIL import Image
    except Exception as exc:  # pragma: no cover
        raise OptionalDependencyError("Image embedding requires 'pillow'.") from exc

    if _embedding_backend() == "fallback":
        return _fallback_image_embedding(image_bytes)

    try:
        model, processor, device = _load_clip()
        import torch

        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        inputs = processor(images=img, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            features = model.get_image_features(**inputs)
        vec = features.detach().cpu().numpy()[0]
        return _l2_normalize(vec)
    except OptionalDependencyError:
        return _fallback_image_embedding(image_bytes)
