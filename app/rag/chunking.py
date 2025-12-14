from __future__ import annotations

from typing import Iterable, List


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> List[str]:
    cleaned = " ".join(text.replace("\n", " ").split())
    if not cleaned:
        return []
    chunks: List[str] = []
    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + chunk_size)
        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(cleaned):
            break
        start = max(end - overlap, 0)
    return chunks


def chunk_with_metadata(text: str, source: str, chunk_size: int = 900, overlap: int = 150) -> Iterable[dict]:
    for index, chunk in enumerate(chunk_text(text, chunk_size=chunk_size, overlap=overlap)):
        yield {
            "source": source,
            "text": chunk,
            "chunk_id": f"{source}:{index}",
        }
