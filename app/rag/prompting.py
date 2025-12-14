from __future__ import annotations

from typing import List, Dict


def build_rag_prompt(question: str, chunks: List[Dict[str, object]]) -> str:
    sources = "\n".join([f"[{chunk.get('source')}] {chunk.get('text')}" for chunk in chunks])
    prompt = (
        "You are a factual assistant. Answer using ONLY the documents below, "
        "do not hallucinate. "
        "If the answer cannot be found, reply 'Not enough information in the documents'.\n\n"
        "Document context:\n"
        f"{sources}\n\n"
        "Question:\n"
        f"{question}\n\n"
        "Answer with citations like [source]."
    )
    return prompt
