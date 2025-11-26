"""Shared explainability helpers (stub)."""

from __future__ import annotations

from typing import Any


def safe_import_shap() -> Any | None:
    try:
        import shap  # type: ignore
        return shap
    except Exception:
        return None


__all__ = ["safe_import_shap"]
