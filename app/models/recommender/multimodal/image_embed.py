from __future__ import annotations

import functools
from typing import Iterable

import numpy as np


class OptionalDependencyError(RuntimeError):
    pass


@functools.lru_cache(maxsize=1)
def _load_clip() -> tuple[object, object, str]:
    """Load CLIP model + processor lazily.

    We keep everything behind a lazy loader so importing this module doesn't
    download weights or pull in heavy deps.
    """
    try:
        import torch
        from transformers import CLIPModel, CLIPProcessor
    except Exception as exc:  # pragma: no cover
        raise OptionalDependencyError(
            "Multimodal recommender requires 'torch' and 'transformers'."
        ) from exc

    device = "cuda" if torch.cuda.is_available() else "cpu"
    # Important: never download weights at runtime. If weights are missing locally,
    # callers should treat this module as unavailable and fall back to other logic.
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32", local_files_only=True).to(device)
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32", local_files_only=True)
    model.eval()
    return model, processor, device


def _l2_normalize(vec: np.ndarray) -> np.ndarray:
    denom = float(np.linalg.norm(vec) + 1e-12)
    return (vec / denom).astype(np.float32)


def embed_text(text: str) -> np.ndarray:
    model, processor, device = _load_clip()
    import torch

    inputs = processor(text=[text], return_tensors="pt", padding=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        features = model.get_text_features(**inputs)
    vec = features.detach().cpu().numpy()[0]
    return _l2_normalize(vec)


def embed_image_pil(image) -> np.ndarray:
    """Embed a PIL image as a unit-norm vector."""
    model, processor, device = _load_clip()
    import torch

    inputs = processor(images=image, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        features = model.get_image_features(**inputs)
    vec = features.detach().cpu().numpy()[0]
    return _l2_normalize(vec)


def embed_image_bytes(image_bytes: bytes) -> np.ndarray:
    try:
        from PIL import Image
    except Exception as exc:  # pragma: no cover
        raise OptionalDependencyError("Multimodal recommender requires 'pillow'.") from exc

    import io

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return embed_image_pil(img)


def stack_embeddings(embeddings: Iterable[np.ndarray]) -> np.ndarray:
    arr = np.stack(list(embeddings), axis=0).astype(np.float32)
    return arr
