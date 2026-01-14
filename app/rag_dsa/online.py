from __future__ import annotations

import json
from typing import List, Optional

from app.rag_dsa.config import settings


def _openai_client():
    if not settings.OPENAI_API_KEY:
        return None
    try:
        from openai import OpenAI

        return ("v1", OpenAI(api_key=settings.OPENAI_API_KEY))
    except Exception:
        try:
            import openai

            openai.api_key = settings.OPENAI_API_KEY
            return ("legacy", openai)
        except Exception:
            return None


def online_enabled() -> bool:
    return settings.ONLINE_MODE and bool(settings.OPENAI_API_KEY)


def _extract_json_list(text: str) -> Optional[List[str]]:
    text = text.strip()
    if not text.startswith("["):
        return None
    try:
        data = json.loads(text)
    except Exception:
        return None
    if not isinstance(data, list):
        return None
    return [str(item).strip() for item in data if str(item).strip()]


def rewrite_queries_online(query: str) -> Optional[List[str]]:
    if not online_enabled():
        return None
    client_info = _openai_client()
    if client_info is None:
        return None

    prompt = (
        "Rewrite the user question into 4 short search queries for DSA notes. "
        "Use diverse wording and key terms. Return ONLY a JSON list of strings.\n\n"
        f"Question: {query}"
    )

    mode, client = client_info
    try:
        if mode == "v1":
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            content = response.choices[0].message.content or ""
        else:
            response = client.ChatCompletion.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            content = response["choices"][0]["message"]["content"] or ""
    except Exception:
        return None

    return _extract_json_list(content)


def rerank_online(query: str, candidates: List[str], top_k: int) -> Optional[List[int]]:
    if not online_enabled() or not candidates:
        return None
    client_info = _openai_client()
    if client_info is None:
        return None

    blocks = []
    for idx, text in enumerate(candidates):
        snippet = text.replace("\n", " ")[:320]
        blocks.append(f"{idx}. {snippet}")

    prompt = (
        "You are reranking retrieved context chunks for a DSA tutor. "
        "Pick the most relevant chunks for the user query. "
        "Return ONLY a JSON list of indices, most relevant first.\n\n"
        f"Query: {query}\n\nCandidates:\n" + "\n".join(blocks)
    )

    mode, client = client_info
    try:
        if mode == "v1":
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            content = response.choices[0].message.content or ""
        else:
            response = client.ChatCompletion.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            content = response["choices"][0]["message"]["content"] or ""
    except Exception:
        return None

    indexes = _extract_json_list(content)
    if indexes is None:
        return None
    ordered = []
    for item in indexes:
        try:
            ordered.append(int(item))
        except Exception:
            continue
    ordered = [i for i in ordered if 0 <= i < len(candidates)][:top_k]
    return ordered
