"""Utility stubs for vision pipelines (transforms, small helpers)."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple


def ensure_vision_root(path: str | Path) -> Path:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Vision root not found: {p}")
    return p


__all__ = ["ensure_vision_root"]
