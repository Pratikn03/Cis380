"""
Recommender prediction module.
"""
from typing import List, Dict, Any, Optional

def recommend(user_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
    # Mock implementation for fallback
    return [
        {"item_id": f"item_{i}", "title": f"Recommended Item {i}", "score": 0.9 - i * 0.1}
        for i in range(top_k)
    ]

def predict_multimodal(
    text: Optional[str] = None,
    image_bytes: Optional[bytes] = None,
    top_k: int = 5
) -> Dict[str, Any]:
    # Mock implementation
    return {
        "items": [
            {"item_id": f"mm_item_{i}", "title": f"Multimodal Item {i}", "score": 0.95 - i * 0.05, "image_path": f"path/to/img_{i}.jpg"}
            for i in range(top_k)
        ],
        "explanation": "Matched based on visual and textual features."
    }