from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


@dataclass
class EmbeddedCorpus:
    docs: list[dict[str, str]]
    vectorizer: TfidfVectorizer
    matrix: np.ndarray


def embed_documents(docs: Iterable[dict[str, str]]) -> EmbeddedCorpus:
    """Return TF-IDF vectors for each document."""
    doc_list = list(docs)
    vectorizer = TfidfVectorizer(stop_words="english")
    texts = [doc["text"] for doc in doc_list]
    matrix = vectorizer.fit_transform(texts).toarray() if texts else np.zeros((0, 0))
    return EmbeddedCorpus(docs=doc_list, vectorizer=vectorizer, matrix=matrix)
