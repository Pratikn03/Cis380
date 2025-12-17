"""Multimodal recommender helpers (image + text similarity).

Design goals:
- Lightweight imports: no model downloads at import time.
- Optional dependencies: works even if CLIP/FAISS aren't installed.
"""

from .types import MultimodalResult, SearchHit

__all__ = ["MultimodalResult", "SearchHit"]
