"""Lightweight RAG service using TF-IDF over local docs."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Could not read %s: %s", path, exc)
        return ""


def _read_pdf(path: Path) -> str:
    try:
        import PyPDF2

        text = []
        with path.open("rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text() or ""
                text.append(page_text)
        return "\n".join(text)
    except Exception as exc:  # pragma: no cover - optional dependency
        logger.warning("Could not read pdf %s: %s", path, exc)
        return ""


def _chunk(text: str) -> List[str]:
    # split by blank lines, then optionally split long paragraphs by sentence
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: List[str] = []
    for p in parts:
        if len(p) > 1200:
            chunks.extend([s.strip() for s in re.split(r"(?<=[.!?])\s+", p) if s.strip()])
        else:
            chunks.append(p)
    return chunks


@dataclass(frozen=True)
class Passage:
    text: str
    source: str
    chunk_id: str


@dataclass
class RagResult:
    query: str
    passages: List[Tuple[Passage, float]]

    def best_text(self) -> str:
        return "\n\n".join(p.text for p, _ in self.passages)


class RagService:
    """Minimal TF-IDF retriever over local docs (data/docs)."""

    def __init__(self, docs_dir: Path = Path("data/docs")):
        self.docs_dir = Path(docs_dir)
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.passages: List[Passage] = []
        self.matrix = None

    def _load_docs(self) -> List[tuple[str, str]]:
        texts: List[tuple[str, str]] = []
        if not self.docs_dir.exists():
            logger.info("Docs folder %s not found; skipping RAG load.", self.docs_dir)
            return texts
        for path in sorted(self.docs_dir.glob("**/*")):
            if path.is_dir():
                continue
            if path.suffix.lower() in {".txt", ".md"}:
                text = _read_text(path)
            elif path.suffix.lower() == ".pdf":
                text = _read_pdf(path)
            else:
                continue
            if text:
                rel = str(path.relative_to(self.docs_dir))
                texts.append((rel, text))
        return texts

    def build(self) -> None:
        texts = self._load_docs()
        for source, t in texts:
            for idx, chunk in enumerate(_chunk(t)):
                chunk_id = f"{source}#{idx}"
                self.passages.append(Passage(text=chunk, source=source, chunk_id=chunk_id))
        if not self.passages:
            logger.warning("No docs found for RAG index.")
            return
        self.matrix = self.vectorizer.fit_transform([p.text for p in self.passages])
        logger.info("Built RAG index with %d passages.", len(self.passages))

    def _ensure_index(self) -> bool:
        if self.matrix is None:
            self.build()
        return self.matrix is not None

    def query(self, query: str, top_k: int = 3) -> RagResult:
        if not self._ensure_index():
            return RagResult(query=query, passages=[])
        q_vec = self.vectorizer.transform([query])
        sims = (self.matrix @ q_vec.T).toarray().ravel()
        idx = np.argsort(sims)[::-1][:top_k]
        passages = [(self.passages[i], float(sims[i])) for i in idx if sims[i] > 0]
        return RagResult(query=query, passages=passages)

    def answer(self, query: str) -> str:
        result = self.query(query, top_k=3)
        if not result.passages:
            return "I could not find anything in your local docs. Add files under data/docs/."
        return result.best_text()


# shared singleton
rag_service = RagService()
