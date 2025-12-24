"""Utility helpers for the Streamlit chatbot."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, List


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


def call_with_container_width(
    fn: Callable[..., Any], /, *args: Any, stretch: bool = True, **kwargs: Any
) -> Any:
    """Call a Streamlit element using the non-deprecated width API when available.

    Streamlit is deprecating `use_container_width` in favor of `width='stretch'`.
    This helper prefers the new API while remaining compatible with older versions.
    """

    if "width" in kwargs or "use_container_width" in kwargs:
        return fn(*args, **kwargs)

    width_value: Any = "stretch" if stretch else "content"
    try:
        return fn(*args, **kwargs, width=width_value)
    except TypeError as exc:
        message = str(exc)
        if "width" not in message and "container_width" not in message:
            raise
    return fn(*args, **kwargs, use_container_width=stretch)


__all__ = ["call_with_container_width", "load_sample_inputs"]
