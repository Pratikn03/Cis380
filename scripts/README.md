# Scripts Workspace

## Purpose
Provide canonical script entrypoints for training, validation, production checks, and utility workflows.

## Scope
- Training orchestration scripts
- Data quality scripts
- Production readiness scripts
- Specialized script groups (`stt`, `voice`, `experimental`)

## Run locally
```bash
python3 scripts/train_all.py
python3 scripts/train_all_vision.py
python3 scripts/check_production.py
python3 scripts/training_data_audit.py
```

## Test and quality commands
```bash
python3 scripts/data/run_quality_gates.py
python3 scripts/quality/docs_quality_check.py --mode fast --threshold 85
```

## Ownership and canonical links
- Owner: Sentifargo Platform Engineering
- Last verified: 2026-02-11
- Canonical repository docs: `../docs/README.md`
- Training operations: `../TRAINING.md`
- Data registry: `../DATASETS.md`
