# Dataset Registry

## Purpose
Define canonical dataset layout, validation expectations, and active dataset roots.

## Scope
- Raw/interim/processed data structure
- Required validation artifacts
- Active dataset locations for training and inference

## Run locally
### Standard validation
```bash
python3 scripts/data/validate_catalog.py --strict
python3 scripts/data/validate_dataset.py --task <task> --dataset <dataset> --path <path>
```

### Split generation
```bash
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
- Canonical docs index: `docs/README.md`
- Canonical style policy: `docs/STYLE_GUIDE.md`

## Standard layout
- `data/raw/<task>/<dataset>/`
- `data/interim/<task>/<dataset>/`
- `data/processed/<task>/<dataset>/`
- `data/splits/<task>/<dataset>/splits.json`
- `data/docs/` (general RAG sources)
- `data/dsa_docs/` (DSA RAG sources)

## Active dataset roots
- `data/raw/fraud/creditcard.csv`
- `data/raw/cyber/`
- `data/raw/behavior/`
- `data/raw/vision/`
- `data/raw/brand/`
- `data/raw/voice/`
- `data/raw/stt/`
- `data/raw/recommendation/`
- `data/raw/dsa/`
