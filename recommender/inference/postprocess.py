"""Postprocessing utilities for recommendations."""
from __future__ import annotations

from typing import List, Any


def postprocess(indices, items: List[Any]):
    return [items[i] for i in indices if i < len(items)]
