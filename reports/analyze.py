"""
Local vision analysis module.
"""

from typing import Dict, Any


def analyze_image_bytes(image_bytes: bytes) -> Dict[str, Any]:
    # Mock implementation
    return {
        "label": "object",
        "confidence": 0.92,
        "description": "An object detected in the image.",
    }
