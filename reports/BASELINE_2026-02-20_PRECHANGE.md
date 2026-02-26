# Baseline Snapshot (2026-02-20)

Captured before committing dashboard/training fixes on branch `fix-dashboard-audit-2026-02-20`.

## Monitor `risk_summary` contract (pre-change)

- `HEAD:app/monitoring/schemas.py` expected:
  - `window`
  - `risk_score`
  - `details`
- `HEAD:app/monitoring/service.py#get_risk_summary` returned:
  - `total_events`
  - `decision_counts`
  - `avg_risks`

This schema mismatch explains the `risk_summary` response validation failure path.

## Training overview domain coverage (pre-change)

- `HEAD:app/api/v1/training.py`:
  - `CORE_DOMAINS = ("fraud", "cyber", "behavior", "vision", "fusion")`
  - Domain total: `5`

## Report artifact timestamps (pre-regeneration)

- `reports/TRAINING_DATA.json`: `2026-02-15 17:49:01 CST`
- `reports/TRAINING_DATA.md`: `2026-02-15 17:49:01 CST`
- `reports/TRAINING_GAPS.json`: `2026-01-21 23:37:40 CST`
- `reports/TRAINING_GAPS.md`: `2026-01-21 23:37:40 CST`
- `reports/PROJECT_AUDIT.json`: `2026-01-21 23:37:40 CST`
- `reports/PROJECT_AUDIT.md`: `2026-01-21 23:37:40 CST`
