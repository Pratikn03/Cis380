# Data Workspace

## Purpose
Define data directory conventions for raw inputs, processed artifacts, splits, and retrieval stores.

## Scope
- Dataset storage layout
- RAG knowledge sources
- Embedding and monitoring outputs

## Run locally
```bash
python3 scripts/data/validate_catalog.py --strict
python3 scripts/data/validate_dataset.py --task <task> --dataset <dataset> --path <path>
python3 scripts/data/make_splits.py --task <task> --dataset <dataset> --path <path>
```

## Test and quality commands
```bash
python3 scripts/data/run_quality_gates.py
python3 scripts/training_data_audit.py
```

## Ownership and canonical links
- Owner: Sentifargo Data Team
- Last verified: 2026-02-11
- Canonical dataset registry: `../DATASETS.md`
- Canonical docs index: `../docs/README.md`

## Layout
- `data/raw/`
- `data/interim/`
- `data/processed/`
- `data/splits/`
- `data/docs/`
- `data/dsa_docs/`
- `data/embeddings/`
- `data/monitoring/`
