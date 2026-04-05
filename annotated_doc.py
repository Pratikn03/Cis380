"""Local compatibility shim for FastAPI's optional `annotated_doc` dependency.

This avoids environment-specific import failures when the site-packages module
is unavailable or blocked.
"""

from __future__ import annotations


class Doc:
    """Simple metadata container used inside `typing.Annotated`."""

    def __init__(self, documentation: str) -> None:
        self.documentation = str(documentation)

    def __repr__(self) -> str:
        return f"Doc({self.documentation!r})"
