from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from app.rag.chunking import chunk_with_metadata
from app.rag.config import settings
from app.rag.dsa_pipeline import ingest_documents


def _read_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".json", ".csv", ".html", ".htm"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    raise ValueError("Unsupported file type for ingestion: %s" % suffix)


def ingest_from_paths(paths: Iterable[Path], chunk_size: int = 900, overlap: int = 150) -> int:
    # Legacy path: chunk raw text files and build embeddings index
    all_chunks: List[dict] = []
    for path in paths:
        content = _read_file(path)
        for chunk in chunk_with_metadata(
            content, source=str(path), chunk_size=chunk_size, overlap=overlap
        ):
            all_chunks.append(chunk)
    if not all_chunks:
        return 0
    ingest_documents(list(paths))
    return len(all_chunks)


def ingest_all_docs() -> int:
    stats = ingest_documents()
    return stats.get("chunks", 0)
