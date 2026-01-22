from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def tokenize(text: str) -> List[str]:
    return TOKEN_RE.findall(text.lower())


@dataclass
class BM25Index:
    doc_ids: List[str]
    doc_freqs: List[Dict[str, int]]
    doc_lens: List[int]
    idf: Dict[str, float]
    avgdl: float
    k1: float = 1.5
    b: float = 0.75

    @classmethod
    def from_texts(cls, doc_ids: List[str], texts: Iterable[str]) -> "BM25Index":
        doc_freqs: List[Dict[str, int]] = []
        doc_lens: List[int] = []
        df: Dict[str, int] = {}
        for text in texts:
            tokens = tokenize(text)
            freqs: Dict[str, int] = {}
            for tok in tokens:
                freqs[tok] = freqs.get(tok, 0) + 1
            doc_freqs.append(freqs)
            doc_lens.append(len(tokens))
            for tok in freqs:
                df[tok] = df.get(tok, 0) + 1
        n_docs = len(doc_freqs)
        avgdl = sum(doc_lens) / n_docs if n_docs else 0.0
        idf = {tok: math.log(1 + (n_docs - freq + 0.5) / (freq + 0.5)) for tok, freq in df.items()}
        return cls(doc_ids=doc_ids, doc_freqs=doc_freqs, doc_lens=doc_lens, idf=idf, avgdl=avgdl)

    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        if not self.doc_freqs:
            return []
        tokens = tokenize(query)
        scores = [0.0] * len(self.doc_freqs)
        for tok in tokens:
            tok_idf = self.idf.get(tok, 0.0)
            if tok_idf == 0.0:
                continue
            for i, freqs in enumerate(self.doc_freqs):
                tf = freqs.get(tok, 0)
                if tf == 0:
                    continue
                denom = tf + self.k1 * (
                    1 - self.b + self.b * (self.doc_lens[i] / (self.avgdl or 1.0))
                )
                score = tok_idf * (tf * (self.k1 + 1) / denom)
                scores[i] += score
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return ranked[: min(top_k, len(ranked))]

    def save(self, path: Path) -> None:
        payload = {
            "doc_ids": self.doc_ids,
            "doc_freqs": self.doc_freqs,
            "doc_lens": self.doc_lens,
            "idf": self.idf,
            "avgdl": self.avgdl,
            "k1": self.k1,
            "b": self.b,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "BM25Index" | None:
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            doc_ids=payload.get("doc_ids", []),
            doc_freqs=payload.get("doc_freqs", []),
            doc_lens=payload.get("doc_lens", []),
            idf=payload.get("idf", {}),
            avgdl=payload.get("avgdl", 0.0),
            k1=payload.get("k1", 1.5),
            b=payload.get("b", 0.75),
        )
