from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_path(raw: str, root: Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else root / path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RagSettings:
    docs_dir: Path = _resolve_path(os.getenv("RAG_DOCS_DIR", "data/raw/docs"), PROJECT_ROOT)
    legacy_docs_dir: Path = _resolve_path(os.getenv("RAG_LEGACY_DOCS_DIR", "data/docs"), PROJECT_ROOT)
    output_dir: Path = _resolve_path(os.getenv("RAG_OUTPUT_DIR", "data/processed/rag"), PROJECT_ROOT)
    logs_path: Path = _resolve_path(os.getenv("RAG_LOG_PATH", "logs/rag_queries.jsonl"), PROJECT_ROOT)
    embed_model: str = os.getenv("RAG_EMBED_MODEL", "all-MiniLM-L6-v2")

    chunk_size: int = int(os.getenv("RAG_CHUNK_SIZE", "800"))
    chunk_overlap: int = int(os.getenv("RAG_CHUNK_OVERLAP", "120"))

    topk_dense: int = int(os.getenv("RAG_TOPK_DENSE", "12"))
    topk_bm25: int = int(os.getenv("RAG_TOPK_BM25", "12"))
    topk_final: int = int(os.getenv("RAG_TOPK_FINAL", "6"))
    hybrid_alpha: float = float(os.getenv("RAG_HYBRID_ALPHA", "0.6"))
    min_score: float = float(os.getenv("RAG_MIN_SCORE", "0.22"))

    auto_ingest: bool = _to_bool(os.getenv("RAG_AUTO_INGEST", "false"))

    documents_path: Path = None  # type: ignore[assignment]
    pages_path: Path = None  # type: ignore[assignment]
    chunks_path: Path = None  # type: ignore[assignment]
    docstore_path: Path = None  # type: ignore[assignment]
    index_meta_path: Path = None  # type: ignore[assignment]
    bm25_path: Path = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        object.__setattr__(self, "documents_path", self.output_dir / "documents.jsonl")
        object.__setattr__(self, "pages_path", self.output_dir / "pages.jsonl")
        object.__setattr__(self, "chunks_path", self.output_dir / "chunks.jsonl")
        object.__setattr__(self, "docstore_path", self.output_dir / "docstore.jsonl")
        object.__setattr__(self, "index_meta_path", self.output_dir / "index.meta.json")
        object.__setattr__(self, "bm25_path", self.output_dir / "bm25.json")


settings = RagSettings()
