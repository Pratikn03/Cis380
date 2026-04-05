# Benchmarks

## Purpose
Run repeatable end-to-end benchmark suites for routing quality, model behavior, and latency.

## Scope
- Intent detection
- Fraud scoring metrics
- RAG retrieval metrics
- System latency metrics
- Multimodal fusion consistency

## Run locally
```bash
python3 -m benchmarks.benchmark_suite
python3 -m benchmarks.benchmark_suite --verbose --save
```

## Test and quality commands
```bash
python3 -m benchmarks.benchmark_suite --save
python3 scripts/quality/docs_quality_check.py --mode fast --threshold 85
```

## Ownership and canonical links
- Owner: Sentifargo Evaluation Team
- Last verified: 2026-02-11
- Canonical docs index: `../docs/README.md`
- Quality pipeline: `../.github/workflows/quality-gates.yml`
