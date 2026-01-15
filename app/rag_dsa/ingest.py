from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

import json

from app.rag.vector_store import VectorStore
from app.rag_dsa.config import settings
from app.rag_dsa.embeddings import DsaEmbeddingModel

ALLOWED_EXT = {".md", ".txt"}


def _iter_doc_paths(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    return [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in ALLOWED_EXT]


def load_docs(root: Path | None = None) -> List[dict]:
    docs_dir = Path(root) if root is not None else Path(settings.DOCS_DIR)
    docs: List[dict] = []
    for path in _iter_doc_paths(docs_dir):
        rel = path.relative_to(docs_dir).as_posix()
        topic = rel.split("/")[0] if "/" in rel else "misc"
        text = path.read_text(encoding="utf-8", errors="ignore").strip()
        if not text:
            continue
        docs.append(
            {
                "doc_id": rel,
                "source": rel,
                "topic": topic,
                "text": text,
            }
        )
    return docs


def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start = max(end - overlap, 0)
    return chunks


def build_chunks(docs: List[dict]) -> List[dict]:
    chunks: List[dict] = []
    for doc in docs:
        doc_chunks = chunk_text(
            doc["text"],
            chunk_size=settings.CHUNK_SIZE,
            overlap=settings.CHUNK_OVERLAP,
        )
        for idx, chunk in enumerate(doc_chunks):
            chunks.append(
                {
                    "text": chunk,
                    "source": doc["source"],
                    "doc_id": doc["doc_id"],
                    "topic": doc["topic"],
                    "chunk_id": idx,
                }
            )
    return chunks


def _write_index_meta(embed_dir: Path, doc_count: int, chunk_count: int, dim: int) -> None:
    payload = {
        "doc_count": doc_count,
        "chunk_count": chunk_count,
        "embed_dim": dim,
    }
    (embed_dir / "index_meta.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def ingest() -> int:
    docs = load_docs()
    if not docs:
        raise RuntimeError(f"No DSA docs found under {settings.DOCS_DIR}.")
    chunks = build_chunks(docs)
    if not chunks:
        return 0

    model = DsaEmbeddingModel()
    vectors = model.embed([c["text"] for c in chunks])

    metadata = [
        {
            "source": c["source"],
            "doc_id": c["doc_id"],
            "topic": c["topic"],
            "chunk_id": c["chunk_id"],
            "text": c["text"],
        }
        for c in chunks
    ]

    embed_dir = Path(settings.EMBED_DIR)
    embed_dir.mkdir(parents=True, exist_ok=True)
    store = VectorStore(embed_dir)
    store.set_embeddings(metadata, vectors)
    _write_index_meta(embed_dir, len(docs), len(chunks), model.dim)
    return len(chunks)


def index_exists() -> bool:
    embed_dir = Path(settings.EMBED_DIR)
    return (embed_dir / "embeddings.npy").exists() and (embed_dir / "metadata.json").exists()


def ensure_index() -> int:
    if not settings.AUTO_INGEST:
        return 0
    if index_exists():
        return 0
    return ingest()
