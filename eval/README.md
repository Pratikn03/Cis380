# Evaluation Data

## Purpose
Describe evaluation assets and how to run DSA retrieval evaluation checks.

## Scope
- DSA qrels and test data
- Evaluation script invocation

## Run locally
```bash
python3 scripts/rag/evaluate_dsa.py
```

## Test and quality commands
```bash
python3 scripts/rag/evaluate_dsa.py
python3 scripts/quality/docs_quality_check.py --mode fast --threshold 85
```

## Ownership and canonical links
- Owner: Sentifargo Evaluation Team
- Last verified: 2026-02-11
- Canonical docs index: `../docs/README.md`
- Benchmark suite docs: `../benchmarks/README.md`
