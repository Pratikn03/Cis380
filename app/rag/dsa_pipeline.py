from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from app.rag.cleaning import normalize_text, strip_repeated_lines
from app.rag.config import settings
from app.rag.embed import EmbeddingModel
from app.rag.index import RagIndex
from app.rag.loaders import scan_documents, load_document
from app.rag.prompting import build_dsa_prompt
from app.rag.retriever import merge_hybrid_results
from app.rag.security import looks_like_prompt_injection, redact_pii
from app.rag.telemetry import log_event
from app.utils.llm_stub import LLMStub


def ingest_documents(paths: Optional[List[Path]] = None, *, rebuild: bool = False) -> Dict[str, int]:
    docs_dir = settings.docs_dir
    if not docs_dir.exists() and settings.legacy_docs_dir.exists():
        docs_dir = settings.legacy_docs_dir

    if rebuild and settings.output_dir.exists():
        for item in settings.output_dir.iterdir():
            if item.is_file():
                item.unlink()

    files = paths or scan_documents(docs_dir)
    documents: List[DocumentContent] = []
    for file_path in files:
        doc = load_document(file_path)
        if doc:
            documents.append(doc)

    if not documents:
        return {"documents": 0, "pages": 0, "chunks": 0}

    doc_records: List[Dict[str, Any]] = []
    page_records: List[Dict[str, Any]] = []
    chunk_records: List[Dict[str, Any]] = []

    for doc in documents:
        doc_records.append(
            {
                "doc_id": doc.doc_id,
                "source": doc.source,
                "doc_type": doc.doc_type,
                "metadata": doc.metadata,
            }
        )
        page_texts = [normalize_text(p.text) for p in doc.pages]
        page_texts = strip_repeated_lines(page_texts)
        for page, cleaned in zip(doc.pages, page_texts):
            page_records.append(
                {
                    "doc_id": doc.doc_id,
                    "source": doc.source,
                    "page": page.page_num,
                    "text": cleaned,
                }
            )
            if not cleaned:
                continue
            from app.rag.chunking import ChunkingStrategy, auto_chunk, chunk_document

            chunks = auto_chunk(cleaned, source=doc.source, chunk_size=settings.chunk_size)
            if not chunks:
                chunks = chunk_document(
                    cleaned,
                    source=doc.source,
                    strategy=ChunkingStrategy.CHARACTER,
                    chunk_size=settings.chunk_size,
                    overlap=settings.chunk_overlap,
                    min_chunk_size=1,
                )
            for chunk in chunks:
                chunk_records.append(
                    {
                        "doc_id": doc.doc_id,
                        "source": doc.source,
                        "filename": Path(doc.source).name,
                        "page": page.page_num,
                        "chunk_id": f"{doc.doc_id}:{page.page_num}:{chunk.index}",
                        "start_char": chunk.start_char,
                        "end_char": chunk.end_char,
                        "text": normalize_text(chunk.text),
                    }
                )

    settings.output_dir.mkdir(parents=True, exist_ok=True)
    _write_jsonl(settings.documents_path, doc_records)
    _write_jsonl(settings.pages_path, page_records)
    _write_jsonl(settings.chunks_path, chunk_records)

    RagIndex.build(chunk_records, model_name=settings.embed_model)

    try:
        from app.db.models import Document, RagChunk
        from app.db.session import SessionLocal

        with SessionLocal() as db:
            db.query(Document).delete()
            db.query(RagChunk).delete()
            db.add_all(
                [
                    Document(
                        id=doc["doc_id"],
                        filename=Path(str(doc["source"])).name,
                        content_hash=doc["doc_id"],
                        source=str(doc.get("source", "")),
                    )
                    for doc in doc_records
                ]
            )
            db.add_all(
                [
                    RagChunk(
                        chunk_id=chunk["chunk_id"],
                        doc_id=chunk["doc_id"],
                        meta={
                            "source": chunk.get("source"),
                            "page": chunk.get("page"),
                            "filename": chunk.get("filename"),
                        },
                    )
                    for chunk in chunk_records
                ]
            )
            db.commit()
    except Exception:
        pass
    return {
        "documents": len(doc_records),
        "pages": len(page_records),
        "chunks": len(chunk_records),
    }


def answer_query(query: str, *, top_k: Optional[int] = None) -> Dict[str, Any]:
    start = time.perf_counter()
    failure_reason = None
    top_k = top_k or settings.topk_final
    if not settings.output_dir.exists() or not (settings.output_dir / "embeddings.npy").exists():
        if settings.auto_ingest:
            ingest_documents()
        else:
            failure_reason = "no_index"
            log_event(
                {
                    "event": "rag_query",
                    "status": "no_index",
                    "query": query,
                    "latency_ms": round((time.perf_counter() - start) * 1000, 2),
                }
            )
            return {
                "answer": "No document index available. Please ingest documents first.",
                "citations": [],
                "confidence": 0.0,
                "retrieval": {"top_score": 0.0, "avg_score": 0.0},
                "sources": [],
            }

    index = RagIndex.load()
    model = EmbeddingModel(model_name=settings.embed_model)
    query_vec = model.embed([query])
    dense = index.search_dense(query_vec[0], top_k=settings.topk_dense)
    bm25 = index.search_bm25(query, top_k=settings.topk_bm25)
    merged = merge_hybrid_results(
        dense,
        bm25,
        top_k=top_k,
        alpha=settings.hybrid_alpha,
    )

    if settings.block_prompt_injection:
        merged = [
            item for item in merged if not looks_like_prompt_injection(str(item.get("text", "")))
        ]

    if settings.redact_pii:
        for item in merged:
            if "text" in item:
                item["text"] = redact_pii(str(item["text"]))

    if not merged:
        failure_reason = "no_evidence"
        log_event(
            {
                "event": "rag_query",
                "status": "no_evidence",
                "query": query,
                "latency_ms": round((time.perf_counter() - start) * 1000, 2),
            }
        )
        return {
            "answer": "Not enough evidence in the documents.",
            "citations": [],
            "confidence": 0.0,
            "retrieval": {"top_score": 0.0, "avg_score": 0.0},
            "sources": [],
        }

    max_score = max(item.get("hybrid_score", 0.0) for item in merged)
    avg_score = sum(item.get("hybrid_score", 0.0) for item in merged) / max(len(merged), 1)
    if max_score < settings.min_score or avg_score < settings.min_avg_score:
        failure_reason = "low_confidence"
        log_event(
            {
                "event": "rag_query",
                "status": "low_confidence",
                "query": query,
                "latency_ms": round((time.perf_counter() - start) * 1000, 2),
                "top_score": max_score,
                "avg_score": avg_score,
            }
        )
        return {
            "answer": "Not enough evidence in the documents.",
            "citations": [],
            "confidence": max_score,
            "retrieval": {"top_score": round(max_score, 4), "avg_score": round(avg_score, 4)},
            "sources": [],
        }

    prompt = build_dsa_prompt(query, merged)
    llm = LLMStub()
    generation_start = time.perf_counter()
    answer = llm.generate(prompt, context=[m.get("text", "") for m in merged])
    generation_ms = (time.perf_counter() - generation_start) * 1000
    if not re.search(r"\[\d+\]", answer):
        citations_hint = ", ".join(f"[{idx}]" for idx in range(1, len(merged) + 1))
        answer = f"{answer}\n\nSources: {citations_hint}"

    citations = [
        {
            "doc_id": item.get("doc_id"),
            "filename": item.get("filename") or Path(str(item.get("source") or "")).name,
            "source": item.get("source"),
            "page": item.get("page"),
            "chunk_id": item.get("chunk_id"),
            "score": item.get("hybrid_score", item.get("score")),
            "snippet": str(item.get("text", "")).replace("\n", " ")[:240],
        }
        for item in merged
    ]

    confidence = min(1.0, max_score + 0.15 * (len(merged) / max(settings.topk_final, 1)))
    latency_ms = (time.perf_counter() - start) * 1000
    retrieve_ms = (time.perf_counter() - start) * 1000 - generation_ms
    retrieval = {"top_score": round(max_score, 4), "avg_score": round(avg_score, 4)}
    _log_query(
        query=query,
        answer=answer,
        latency_ms=latency_ms,
        citations=citations,
        confidence=confidence,
        retrieve_ms=retrieve_ms,
        generation_ms=generation_ms,
        failure_reason=failure_reason,
        chunk_scores=[(c.get("chunk_id"), c.get("hybrid_score")) for c in merged],
    )
    return {
        "answer": answer,
        "citations": citations,
        "confidence": round(confidence, 4),
        "retrieval": retrieval,
        "sources": merged,
        "latency_ms": round(latency_ms, 2),
    }


def delete_document(doc_id: str) -> Dict[str, Any]:
    if not settings.documents_path.exists():
        return {"status": "missing", "message": "No documents index found."}
    records = [
        json.loads(line)
        for line in settings.documents_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    target = next((r for r in records if r.get("doc_id") == doc_id), None)
    if not target:
        return {"status": "missing", "message": f"doc_id {doc_id} not found."}
    source = target.get("source")
    if source:
        path = Path(source)
        if path.exists():
            path.unlink()
    stats = ingest_documents(rebuild=True)
    return {"status": "deleted", "doc_id": doc_id, **stats}


def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _log_query(
    *,
    query: str,
    answer: str,
    latency_ms: float,
    citations: List[Dict[str, Any]],
    confidence: float,
    retrieve_ms: float,
    generation_ms: float,
    failure_reason: Optional[str],
    chunk_scores: List[tuple],
) -> None:
    payload = {
        "query": query,
        "answer_preview": answer[:400],
        "latency_ms": round(latency_ms, 2),
        "retrieve_ms": round(retrieve_ms, 2),
        "generation_ms": round(generation_ms, 2),
        "citations": citations,
        "confidence": round(confidence, 4),
        "failure_reason": failure_reason,
        "chunk_scores": chunk_scores,
    }
    log_event(payload)
if TYPE_CHECKING:
    from app.rag.loaders import DocumentContent
