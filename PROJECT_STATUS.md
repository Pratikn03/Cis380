# Project Status

## Purpose
Manual advisory index for the training and monitoring surface.

This file is not the source of truth for release readiness. Use the generated evidence files instead.

## Canonical evidence
- `reports/TRAINING_DATA.json`
- `reports/TRAINING_DATA.md`
- `reports/TRAINING_GAPS.json`
- `reports/TRAINING_GAPS.md`
- `reports/core_training_gate.json`
- `reports/extended_training_gate.json`
- `reports/ARTIFACT_GATE.json`
- `reports/ARTIFACT_GATE.md`

## Canonical status vocabulary
- `ready`
- `degraded`
- `blocked`
- `advisory`

Legacy reports may still surface raw labels such as `ok`, `warn`, `missing`, `green`, `yellow`, or `red`, but those are preserved only as evidence. The canonical readiness signal is the `readiness_status` field in the generated reports.

## Voice source
- Canonical voice source: `processed_balanced`
- Raw voice tree remains the upstream source for balanced derivation.
- Advisory evidence for voice readiness lives in `reports/TRAINING_DATA.json` and `reports/TRAINING_GAPS.json`.

## Manual notes
- Fraud, cyber, behavior, vision, RAG, DSA RAG, and recommender are all tracked through generated readiness evidence.
- Historical markdown summaries are retained for reference only.
- Any final sign-off must use the release bar once it is generated.

## Regenerate evidence
```bash
python3 scripts/training_data_audit.py
python3 scripts/training_gap_report.py
python3 scripts/training_preflight.py
python3 scripts/training_two_tier_gate.py
```
