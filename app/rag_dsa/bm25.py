from __future__ import annotations

import math
from typing import Iterable, List

from app.rag_dsa.utils import tokenize


class BM25Index:
    """Lightweight BM25 index for offline retrieval."""

    def __init__(self, texts: Iterable[str], k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.docs = [tokenize(t) for t in texts]
        self.doc_lens = [len(d) for d in self.docs]
        self.avgdl = sum(self.doc_lens) / len(self.doc_lens) if self.doc_lens else 0.0
        self.df = {}
        for doc in self.docs:
            seen = set()
            for term in doc:
                if term in seen:
                    continue
                seen.add(term)
                self.df[term] = self.df.get(term, 0) + 1
        self.num_docs = len(self.docs)

    def _idf(self, term: str) -> float:
        df = self.df.get(term, 0)
        if df == 0 or self.num_docs == 0:
            return 0.0
        return math.log(1 + (self.num_docs - df + 0.5) / (df + 0.5))

    def scores(self, query: str) -> List[float]:
        tokens = tokenize(query)
        scores = [0.0 for _ in self.docs]
        if not tokens:
            return scores
        for i, doc in enumerate(self.docs):
            if not doc:
                continue
            freqs = {}
            for term in doc:
                freqs[term] = freqs.get(term, 0) + 1
            denom_base = 1 - self.b + self.b * (len(doc) / self.avgdl) if self.avgdl else 1.0
            for term in tokens:
                tf = freqs.get(term, 0)
                if tf == 0:
                    continue
                idf = self._idf(term)
                score = idf * (tf * (self.k1 + 1)) / (tf + self.k1 * denom_base)
                scores[i] += score
        return scores
