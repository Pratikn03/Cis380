"""
Multimodal recommender prediction module.
"""

from typing import Optional, Dict, Any


class IndexNotBuiltError(Exception):
    pass


def multimodal_recommend(
    image_bytes: Optional[bytes] = None, text: Optional[str] = None, top_k: int = 5
) -> Dict[str, Any]:
    # Mock implementation
    return {
        "items": [
            {"item_id": f"mm_item_{i}", "title": f"Multimodal Item {i}", "score": 0.95 - i * 0.05}
            for i in range(top_k)
        ],
        "explanation": "Matched based on visual and textual features.",
    }
