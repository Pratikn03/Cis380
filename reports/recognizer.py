"""
Brand recognition module.
"""

from typing import List, Dict, Any


def predict_image_bytes(
    image_bytes: bytes, conf: float = 0.25, kind: str = "logo"
) -> List[Dict[str, Any]]:
    # Mock implementation
    return [{"brand": "BrandX", "confidence": 0.95, "bbox": [10, 10, 100, 100]}]


def model_path(kind: str = "logo") -> str:
    return f"models/brand/{kind}.pt"


def available_model_kinds() -> List[str]:
    return ["logo", "car", "fashion"]
