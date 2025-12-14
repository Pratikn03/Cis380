from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

from app.rag.chunking import chunk_with_metadata
from app.rag.embed import EmbeddingModel
from app.rag.vector_store import VectorStore

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT.parent / "docs"
EMBED_DIR = ROOT.parent / "data" / "embeddings"


def _read_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8")
    if suffix == ".json":
        return path.read_text(encoding="utf-8")
    raise ValueError("Unsupported file type for ingestion: %s" % suffix)


def ingest_from_paths(paths: Iterable[Path], chunk_size: int = 900, overlap: int = 150) -> int:
    all_chunks: List[dict] = []
    for path in paths:
        content = _read_file(path)
        for chunk in chunk_with_metadata(content, source=str(path), chunk_size=chunk_size, overlap=overlap):
            all_chunks.append(chunk)
    if not all_chunks:
        return 0
    texts = [chunk["text"] for chunk in all_chunks]
    model = EmbeddingModel()
    embeddings = model.embed(texts)
    metadata = [
        {"source": chunk["source"], "chunk_id": chunk["chunk_id"], "text": chunk["text"]}
        for chunk in all_chunks
    ]
    store = VectorStore(EMBED_DIR)
    store.set_embeddings(metadata, embeddings)
    return len(metadata)


def ingest_all_docs() -> int:
    if not DOCS_DIR.exists():
        return 0
    text_files = [p for p in DOCS_DIR.iterdir() if p.suffix.lower() in {".txt", ".md"}]
    return ingest_from_paths(text_files)
