# Documentation Index

## Purpose
Provide a single navigation layer for all authoritative Sentifargo documentation.

## Scope
This index covers architecture, operations, data/reproducibility, security, and model cards.

## Run locally
Render and validate docs from repo root:
```bash
make quality-docs-fast
make quality-docs
```

## Test and quality commands
```bash
python3 scripts/quality/docs_quality_check.py --mode fast --threshold 85
python3 scripts/quality/docs_quality_check.py --mode full --threshold 95
```

## Ownership and canonical links
- Owner: Sentifargo Engineering
- Last verified: 2026-02-11
- Canonical root overview: `../README.md`
- Canonical architecture mapping: `CANONICAL.md`
- Documentation policy: `STYLE_GUIDE.md`

## Documentation map
### Architecture and platform
- `ARCHITECTURE.md`
- `SENTIFARGO_2_0_IMPLEMENTATION.md`
- `TIER5_OVERVIEW.md`
- `TIER6_RUNBOOK.md`

### Security and operations
- `SECURITY.md`
- `PRODUCTION_READINESS_PLAN.md`
- `PRODUCTION_DEPLOYMENT.md`
- `DEPLOY_RENDER.md`

### Data and reproducibility
- `DATASET_DOWNLOADS.md`
- `REPRODUCIBILITY.md`
- `behavior_features.md`
- `vision_labels.md`

### Audits and roadmap
- `PROJECT_AUDIT_2026-01-29.md`
- `MLOPS_ROADMAP.md`

### Model cards
- `model_cards/fraud/MODEL_CARD_20260121.md`
- `model_cards/cyber/MODEL_CARD_20260121.md`
- `model_cards/behavior/MODEL_CARD_20260121.md`
- `model_cards/vision/MODEL_CARD_20260121.md`
- `model_cards/fusion/MODEL_CARD_20260121.md`
- `model_cards/recommender/MODEL_CARD_20260121.md`
