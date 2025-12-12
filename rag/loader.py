"""Readers for documents stored in `data/docs/`."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .service import _read_pdf, _read_text


def load_docs(path: str | Path = Path("data/docs")) -> list[dict[str, str]]:
    """Return a list of documents with `id`, `text`, and `path`."""
    docs_dir = Path(path)
    docs: list[dict[str, str]] = []
    if not docs_dir.exists():
        return docs
    for file in sorted(docs_dir.rglob("*")):
        if file.is_dir():
            continue
        text = ""
        if file.suffix.lower() in {".txt", ".md", ".rst"}:
            text = _read_text(file)
        elif file.suffix.lower() == ".pdf":
            text = _read_pdf(file)
        if not text.strip():
            continue
        docs.append(
            {"id": str(file.relative_to(docs_dir)), "text": text, "path": str(file.resolve())}
        )
    return docs
