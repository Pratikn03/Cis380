from __future__ import annotations

import os


class DsaRagSettings:
    DOCS_DIR = os.getenv("DSA_DOCS_DIR", "data/dsa_docs")
    EMBED_DIR = os.getenv("DSA_EMBED_DIR", "data/dsa_embeddings")
    CACHE_DIR = os.getenv("DSA_CACHE_DIR", "data/processed/cache/dsa")

    ONLINE_MODE = os.getenv("DSA_ONLINE_MODE", "false").lower() == "true"
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("DSA_OPENAI_MODEL", "gpt-4.1-nano")

    EMBED_DIM = int(os.getenv("DSA_EMBED_DIM", "768"))
    CHUNK_SIZE = int(os.getenv("DSA_CHUNK_SIZE", "900"))
    CHUNK_OVERLAP = int(os.getenv("DSA_CHUNK_OVERLAP", "120"))

    TOPK_DENSE = int(os.getenv("DSA_TOPK_DENSE", "12"))
    TOPK_BM25 = int(os.getenv("DSA_TOPK_BM25", "12"))
    TOPK_MERGED = int(os.getenv("DSA_TOPK_MERGED", "24"))
    TOPK_FINAL = int(os.getenv("DSA_TOPK_FINAL", "6"))

    AUTO_INGEST = os.getenv("DSA_AUTO_INGEST", "true").lower() == "true"


settings = DsaRagSettings()
