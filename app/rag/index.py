
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Dict, Any

from app.rag.bm25 import BM25Index
from app.rag.config import settings
from app.rag.embed import EmbeddingModel
from app.rag.vector_store import VectorStore


@dataclass
class RagIndex:
    vector_store: VectorStore
    bm25: BM25Index | None

    @classmethod
    def load(cls) -> "RagIndex":
        store = VectorStore(settings.output_dir)
        bm25 = BM25Index.load(settings.bm25_path)
        return cls(vector_store=store, bm25=bm25)

    @classmethod
    def build(
        cls,
        chunks: List[Dict[str, Any]],
        *,
        model_name: str,
    ) -> "RagIndex":
        texts = [c["text"] for c in chunks]
        model = EmbeddingModel(model_name=model_name)
        embeddings = model.embed(texts)
        metadata = [
            {
                "doc_id": c["doc_id"],
                "source": c["source"],
                "chunk_id": c["chunk_id"],
                "page": c.get("page"),
                "start_char": c.get("start_char"),
                "end_char": c.get("end_char"),
                "text": c["text"],
            }
            for c in chunks
        ]
        store = VectorStore(settings.output_dir)
        store.set_embeddings(metadata, embeddings)
        _write_docstore(metadata, settings.docstore_path)
        doc_count = len({c["doc_id"] for c in chunks})
        _write_index_meta(
            settings.index_meta_path,
            model_name=model_name,
            dim=store.dim or embeddings.shape[1],
            chunks=len(metadata),
            documents=doc_count,
        )
        bm25 = BM25Index.from_texts([c["chunk_id"] for c in chunks], texts)
        bm25.save(settings.bm25_path)
        return cls(vector_store=store, bm25=bm25)

    def search_dense(self, query_vec, top_k: int) -> List[Dict[str, Any]]:
        return self.vector_store.search(query_vec, top_k=top_k)

    def search_bm25(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        if not self.bm25:
            return []
        ranked = self.bm25.search(query, top_k=top_k)
        results = []
        for idx, score in ranked:
            if idx >= len(self.vector_store.metadata):
                continue
            meta = self.vector_store.metadata[idx]
            results.append(
                {
                    "doc_id": meta.get("doc_id"),
                    "source": meta.get("source"),
                    "chunk_id": meta.get("chunk_id"),
                    "page": meta.get("page"),
                    "start_char": meta.get("start_char"),
                    "end_char": meta.get("end_char"),
                    "text": meta.get("text"),
                    "score": float(score),
                }
            )
        return results


def _write_docstore(metadata: Iterable[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for entry in metadata:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _write_index_meta(
    path: Path, *, model_name: str, dim: int, chunks: int, documents: int
) -> None:
    payload = {
        "model_name": model_name,
        "dim": dim,
        "chunks": chunks,
        "documents": documents,
        "built_at": datetime.utcnow().isoformat() + "Z",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
