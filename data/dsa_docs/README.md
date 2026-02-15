# DSA Docs Corpus

## Purpose
Define the document corpus used by the DSA RAG pipeline.

## Scope
- Topic content for DSA retrieval
- Index build and refresh process

## Run locally
```bash
python3 -m app.rag_dsa.build_index
```

## Test and quality commands
```bash
python3 scripts/rag/evaluate_dsa.py
python3 scripts/quality/docs_quality_check.py --mode fast --threshold 85
```

## Ownership and canonical links
- Owner: Sentifargo RAG Team
- Last verified: 2026-02-11
- Canonical docs index: `../../docs/README.md`
- DSA RAG entrypoint: `../../app/rag_dsa/build_index.py`

## Topics
- arrays, searching/sorting, linked lists, stack/queue, trees, graphs, heaps, DP, hashing, recursion/backtracking, greedy, bit manipulation, strings
