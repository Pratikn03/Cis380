"""Parsing and sanitization for chatbot/recommender inputs."""
from __future__ import annotations

import re
from typing import Dict, Any

from .utils import safe_float, try_parse_json


def _parse_key_values(text: str) -> Dict[str, Any]:
    """Parse simple key=value pairs separated by commas or spaces."""
    pairs = re.split(r"[,\n]", text)
    out: Dict[str, Any] = {}
    for pair in pairs:
        if "=" not in pair:
            continue
        k, v = pair.split("=", 1)
        k = k.strip()
        v = v.strip()
        if not k:
            continue
        # Try to cast numeric
        try:
            if re.match(r"^-?\d+(\.\d+)?$", v):
                out[k] = safe_float(v, v)
            else:
                out[k] = v
        except Exception:
            out[k] = v
    return out


def parse_text_to_event(text: str) -> Dict[str, Any]:
    """
    Best-effort parse of user input into an event dict.
    Supports:
    - JSON / Python dict literals
    - key=value pairs separated by commas/newlines
    """
    text = (text or "").strip()
    if not text:
        return {}

    data = try_parse_json(text)
    if isinstance(data, dict) and data:
        return data

    kv = _parse_key_values(text)
    return kv


__all__ = ["parse_text_to_event"]
