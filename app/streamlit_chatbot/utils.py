"""Utility helpers for the Streamlit chatbot."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List


def load_sample_inputs(path: str | Path) -> List[str]:
    p = Path(path)
    if not p.exists():
        return []
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [str(x) for x in data]
        return []
    except Exception:
        return []


__all__ = ["load_sample_inputs"]
