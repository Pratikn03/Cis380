# Synthetic Data Workspace

## Purpose
Document generation of cross-modal synthetic data for fusion-model training and evaluation.

## Scope
- Scenario generation
- JSON/PyTorch export formats
- Synthetic dataset usage patterns

## Run locally
```bash
cd data/synthetic
python3 cross_modal_generator.py
```

## Test and quality commands
```bash
python3 scripts/quality/docs_quality_check.py --mode fast --threshold 85
```

## Ownership and canonical links
- Owner: Sentifargo ML Research
- Last verified: 2026-02-11
- Canonical docs index: `../../docs/README.md`
- Canonical training guide: `../../TRAINING.md`

## Scenario coverage
- Insider threat
- Fraud collision
- Network intrusion
- Voice phishing
