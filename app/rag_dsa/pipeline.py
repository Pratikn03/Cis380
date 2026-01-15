from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List

from app.rag.vector_store import VectorStore
from app.rag_dsa.bm25 import BM25Index
from app.rag_dsa.config import settings
from app.rag_dsa.embeddings import DsaEmbeddingModel
from app.rag_dsa.ingest import build_chunks, ensure_index, load_docs
from app.rag_dsa.online import answer_online, online_enabled
from app.rag_dsa.utils import cache_get, cache_set, stable_hash, tokenize, unique_preserve


_CHATGPT_LINK = "https://chat.openai.com/"

_REWRITE_HINTS = {
    "array": ["array indexing", "dynamic array", "prefix sum", "two pointers"],
    "linked list": ["singly linked list", "doubly linked list", "fast slow pointer"],
    "stack": ["stack lifo", "monotonic stack", "push pop"],
    "queue": ["queue fifo", "deque", "bfs queue"],
    "search": ["linear search", "binary search", "searching time complexity"],
    "sort": ["quicksort", "mergesort", "heapsort", "sorting stability"],
}

_BM25_INDEX: BM25Index | None = None
_BM25_CHUNKS: List[dict] | None = None

_SHORT_ANCHORS = {
    "lca",
    "dp",
    "dfs",
    "bfs",
    "mst",
    "scc",
    "lcs",
    "lcp",
    "lps",
    "dijkstra",
    "kruskal",
    "prim",
}


def rewrite_query(query: str) -> List[str]:
    cache_path = os.path.join(settings.CACHE_DIR, f"rewrite_{stable_hash(query)}.json")
    cached = cache_get(cache_path)
    if cached and isinstance(cached.get("queries"), list):
        return cached["queries"]

    base = query.strip()
    lower = base.lower()
    expansions: List[str] = [base]

    for key, extras in _REWRITE_HINTS.items():
        if key in lower:
            expansions.extend([f"{base} {extra}" for extra in extras])

    expansions.extend([f"{base} time complexity", f"{base} example"])
    deduped = unique_preserve([q for q in expansions if q.strip()])[:4]

    cache_set(cache_path, {"queries": deduped})
    return deduped


def _load_bm25() -> tuple[BM25Index, List[dict]]:
    global _BM25_INDEX, _BM25_CHUNKS
    if _BM25_INDEX is not None and _BM25_CHUNKS is not None:
        return _BM25_INDEX, _BM25_CHUNKS
    docs = load_docs()
    chunks = build_chunks(docs)
    texts = [c["text"] for c in chunks]
    _BM25_INDEX = BM25Index(texts)
    _BM25_CHUNKS = chunks
    return _BM25_INDEX, _BM25_CHUNKS


def dense_retrieve(query: str, top_k: int) -> List[Dict[str, Any]]:
    model = DsaEmbeddingModel()
    vectors = model.embed([query])
    if vectors.size == 0:
        return []
    store = VectorStore(Path(settings.EMBED_DIR))
    results = store.search(vectors[0], top_k=top_k)
    hits = []
    for res in results:
        hits.append(
            {
                "text": res.get("text"),
                "meta": {
                    "source": res.get("source"),
                    "doc_id": res.get("doc_id"),
                    "topic": res.get("topic"),
                    "chunk_id": res.get("chunk_id"),
                },
                "score_dense": float(res.get("score", 0.0)),
                "score_bm25": 0.0,
                "retrievers": {"dense"},
            }
        )
    return hits


def bm25_retrieve(query: str, top_k: int) -> List[Dict[str, Any]]:
    index, chunks = _load_bm25()
    scores = index.scores(query)
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    hits = []
    for idx in ranked:
        chunk = chunks[idx]
        hits.append(
            {
                "text": chunk["text"],
                "meta": {
                    "source": chunk["source"],
                    "doc_id": chunk["doc_id"],
                    "topic": chunk["topic"],
                    "chunk_id": chunk["chunk_id"],
                },
                "score_dense": 0.0,
                "score_bm25": float(scores[idx]),
                "retrievers": {"bm25"},
            }
        )
    return hits


def merge_dedupe(items: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
    merged: Dict[tuple, Dict[str, Any]] = {}
    for item in items:
        meta = item.get("meta", {})
        key = (meta.get("doc_id") or meta.get("source"), meta.get("chunk_id"))
        if key not in merged:
            merged[key] = item
            continue
        existing = merged[key]
        existing["score_dense"] = max(existing.get("score_dense", 0.0), item.get("score_dense", 0.0))
        existing["score_bm25"] = max(existing.get("score_bm25", 0.0), item.get("score_bm25", 0.0))
        existing["retrievers"] = set(existing.get("retrievers", set())) | set(
            item.get("retrievers", set())
        )
    ordered = sorted(
        merged.values(),
        key=lambda h: (h.get("score_dense", 0.0) + h.get("score_bm25", 0.0)),
        reverse=True,
    )
    return ordered[:top_k]


def _candidate_key(candidate: Dict[str, Any]) -> tuple:
    meta = candidate.get("meta", {})
    return (meta.get("doc_id") or meta.get("source"), meta.get("chunk_id"))


def _query_anchors(query: str) -> list[str]:
    anchors = []
    for token in tokenize(query):
        if len(token) >= 4 or token in _SHORT_ANCHORS:
            anchors.append(token)
    return unique_preserve(anchors)


def _query_phrases(query: str) -> list[str]:
    tokens = tokenize(query)
    phrases: list[str] = []
    for size in (2, 3):
        for idx in range(len(tokens) - size + 1):
            phrase = " ".join(tokens[idx : idx + size])
            if phrase and phrase not in phrases:
                phrases.append(phrase)
    return phrases[:8]


def _phrase_hit(phrases: list[str], text: str) -> bool:
    if not phrases or not text:
        return False
    lowered = text.lower()
    return any(p in lowered for p in phrases)


def _apply_grounding_gate(query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not candidates:
        return candidates
    anchors = set(_query_anchors(query))
    phrases = _query_phrases(query)
    if not anchors and not phrases:
        return candidates

    min_required = 1 if len(anchors) <= 1 else 2
    filtered: list[Dict[str, Any]] = []
    for cand in candidates:
        text = cand.get("text") or ""
        tokens = set(tokenize(text))
        match_count = len(anchors & tokens)
        if match_count >= min_required or _phrase_hit(phrases, text):
            filtered.append(cand)

    if not filtered:
        return candidates

    top_bm25 = max(candidates, key=lambda c: c.get("score_bm25", 0.0))
    filtered_keys = {_candidate_key(c) for c in filtered}
    if _candidate_key(top_bm25) not in filtered_keys:
        filtered.append(top_bm25)
    return filtered


def _minmax(values: List[float]) -> List[float]:
    if not values:
        return []
    lo = min(values)
    hi = max(values)
    if hi - lo == 0:
        return [0.0 for _ in values]
    return [(v - lo) / (hi - lo) for v in values]


def rerank(query: str, candidates: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
    candidate_sig = stable_hash(
        "|".join(f"{_candidate_key(c)[0]}:{_candidate_key(c)[1]}" for c in candidates)
    )
    cache_path = os.path.join(
        settings.CACHE_DIR, f"rerank_{stable_hash(query)}_{candidate_sig}.json"
    )
    cached = cache_get(cache_path)
    cached_order = None
    if cached and isinstance(cached.get("order"), list):
        cached_order = cached["order"]

    dense_scores = [c.get("score_dense", 0.0) for c in candidates]
    bm25_scores = [c.get("score_bm25", 0.0) for c in candidates]
    dense_norm = _minmax(dense_scores)
    bm25_norm = _minmax(bm25_scores)

    query_terms = set(tokenize(query))
    anchors = set(_query_anchors(query))
    phrases = _query_phrases(query)
    for idx, cand in enumerate(candidates):
        text = cand.get("text") or ""
        tokens = set(tokenize(text))
        overlap = len(query_terms & tokens) / max(len(query_terms), 1)
        anchor_ratio = len(anchors & tokens) / max(len(anchors), 1) if anchors else 0.0
        phrase_bonus = 0.05 if _phrase_hit(phrases, text) else 0.0
        score = (
            0.4 * dense_norm[idx]
            + 0.3 * bm25_norm[idx]
            + 0.15 * overlap
            + 0.1 * anchor_ratio
            + phrase_bonus
        )
        cand["score_final"] = score

    if cached_order is not None:
        ordered = [candidates[i] for i in cached_order if 0 <= i < len(candidates)]
    else:
        ordered = sorted(candidates, key=lambda c: c.get("score_final", 0.0), reverse=True)
        cache_set(cache_path, {"order": [candidates.index(c) for c in ordered]})

    return ordered[:top_k]


def _split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def answer_with_sources(query: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not sources:
        return {
            "answer": "Not enough information in the DSA documents.",
            "sources": [],
            "citations": [],
            "chatgpt_link": _CHATGPT_LINK,
            "chatgpt_prompt": "",
        }

    query_terms = set(tokenize(query))
    selected: List[tuple[str, int]] = []
    for idx, src in enumerate(sources):
        sentences = _split_sentences(src.get("text") or "")
        for sent in sentences:
            tokens = set(tokenize(sent))
            if query_terms & tokens:
                selected.append((sent, idx))
            if len(selected) >= 5:
                break
        if len(selected) >= 5:
            break

    if not selected:
        top_sentences = _split_sentences(sources[0].get("text") or "")
        selected = [(s, 0) for s in top_sentences[:3]]

    lines = []
    citations = []
    for sent, idx in selected:
        meta = sources[idx].get("meta", {})
        source = meta.get("source") or meta.get("doc_id") or "source"
        chunk_id = meta.get("chunk_id")
        citation = f"{source}#{chunk_id}" if chunk_id is not None else str(source)
        lines.append(f"- {sent} [{source}]")
        citations.append(citation)

    answer = "Key points:\n" + "\n".join(lines)

    ui_sources = []
    for src in sources:
        meta = src.get("meta", {})
        ui_sources.append(
            {
                "topic": meta.get("topic"),
                "source": meta.get("source"),
                "doc_id": meta.get("doc_id"),
                "chunk_id": meta.get("chunk_id"),
                "retrievers": sorted(list(src.get("retrievers", []))),
                "score_dense": src.get("score_dense"),
                "score_bm25": src.get("score_bm25"),
                "score_final": src.get("score_final"),
                "snippet": (src.get("text") or "")[:280].replace("\n", " "),
            }
        )

    context_prompt = "\n\n".join(
        [f"[{i}] {s['snippet']} (source={s['source']})" for i, s in enumerate(ui_sources)]
    )
    chatgpt_prompt = (
        "You are a DSA tutor. Use the context below and answer with citations.\n\n"
        f"Question: {query}\n\nContext:\n{context_prompt}"
    )

    return {
        "answer": answer,
        "sources": ui_sources,
        "citations": citations,
        "chatgpt_link": _CHATGPT_LINK,
        "chatgpt_prompt": chatgpt_prompt,
    }


def _should_fallback_online(candidates: List[Dict[str, Any]]) -> bool:
    if not candidates:
        return True
    top_score = candidates[0].get("score_final")
    if top_score is None:
        return True
    return float(top_score) < settings.ONLINE_FALLBACK_MIN_SCORE


def run_dsa_rag(query: str) -> Dict[str, Any]:
    ensure_index()

    rewritten = rewrite_query(query)
    dense_hits: List[Dict[str, Any]] = []
    bm25_hits: List[Dict[str, Any]] = []

    for q in rewritten:
        dense_hits.extend(dense_retrieve(q, settings.TOPK_DENSE))
        bm25_hits.extend(bm25_retrieve(q, settings.TOPK_BM25))

    merged = merge_dedupe(dense_hits + bm25_hits, settings.TOPK_MERGED)
    grounded = _apply_grounding_gate(query, merged)
    top = rerank(query, grounded, settings.TOPK_FINAL)

    result = answer_with_sources(query, top)
    result["rewritten_queries"] = rewritten
    result["retrieval_counts"] = {
        "dense": len(dense_hits),
        "bm25": len(bm25_hits),
        "merged": len(merged),
    }
    result["online_used"] = False

    if online_enabled() and _should_fallback_online(top):
        online_answer = answer_online(query)
        if online_answer:
            result["answer"] = online_answer
            result["sources"] = []
            result["citations"] = []
            result["chatgpt_prompt"] = ""
            result["online_used"] = True
            result["online_reason"] = "offline_context_insufficient"

    return result
