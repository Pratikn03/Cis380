"""RAG helpers."""

from .config import settings
from .ingest import ingest_all_docs

__all__ = ["ingest_all_docs"]

if settings.auto_ingest:
    _ = ingest_all_docs()
