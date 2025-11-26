"""Extract simple tags from an image using CLIP (torch/torchvision), with safe fallback."""
from __future__ import annotations

from typing import List

try:
    import torch
    import torchvision.transforms as T
    from PIL import Image

    _TORCH_AVAILABLE = True
except Exception as exc:  # noqa: F841
    _TORCH_AVAILABLE = False


def _load_clip_model():
    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = torch.hub.load("openai/clip", "clip_vit_b32", source="github")
    model = model.to(device).eval()
    return model, preprocess, device


def extract_tags_from_image(image, top_k: int = 5) -> List[str]:
    """Return a list of top-k tags for the image. Returns [] on any failure."""
    if not _TORCH_AVAILABLE:
        print("[image_tags] torch/torchvision not available; skipping tag extraction.")
        return []

    try:
        model, preprocess, device = _load_clip_model()
    except Exception as exc:
        print(f"[image_tags] Failed to load CLIP: {exc}")
        return []

    candidate_labels = [
        "formal suit", "business attire", "casual wear", "streetwear", "sportswear",
        "jacket", "hoodie", "dress", "skirt", "jeans", "sneakers", "boots",
        "superhero costume", "sci-fi armor", "fantasy costume", "classic film",
        "summer outfit", "winter outfit",
    ]

    try:
        import clip  # type: ignore
    except Exception as exc:
        print(f"[image_tags] CLIP tokenizer missing: {exc}")
        return []

    try:
        text_tokens = torch.cat([clip.tokenize(l) for l in candidate_labels]).to(device)
        with torch.no_grad():
            img_tensor = preprocess(image).unsqueeze(0).to(device)
            image_features = model.encode_image(img_tensor)
            text_features = model.encode_text(text_tokens)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            logits = image_features @ text_features.t()
            probs = logits.softmax(dim=-1).squeeze(0)

        top_vals, top_idxs = probs.topk(min(top_k, len(candidate_labels)))
        tags = [candidate_labels[idx] for idx in top_idxs.tolist()]
        return tags
    except Exception as exc:
        print(f"[image_tags] Tag extraction failed: {exc}")
        return []


__all__ = ["extract_tags_from_image"]
