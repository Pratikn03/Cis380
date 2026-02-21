# Audit Summary - 2026-02-20

## Scope Completed

- Full training/model audit refresh for data gaps, pipeline contracts, and dashboard-relevant code paths.
- Dashboard backend stabilization (`/api/monitor/risk_summary`, dev auth bootstrap, training overview domain coverage).
- Dashboard UI stabilization across React sidebar/home and Streamlit auth/error handling paths.

## Key Fixes Delivered

1. Monitoring contract fix:
- `GET /api/monitor/risk_summary` now matches typed schema:
  - `window_n`
  - `total_events`
  - `decision_counts`
  - `avg_risks`
- Empty log states return deterministic zero/default values without Pydantic validation failures.

2. Dev/test auth bootstrap reliability:
- Non-production startup now ensures schema creation before auth bootstrap.
- Dev/test fallback bootstrap credentials supported when `ADMIN_USERNAME`/`ADMIN_PASSWORD` are not provided.
- Production behavior remains strict (no implicit fallback bootstrap).

3. Training API coverage expanded to 7 domains:
- Added `voice` and `recommender` to overview/domain endpoints.
- Domain readiness, blockers, model artifact checks, and metrics source resolution updated.

4. Voice pipeline contract alignment:
- Trainer supports canonical `--out-model` output flag.
- Voice verification script aligned with trainer CLI and `predict_emotion(audio_bytes=...)` call contract.

5. Dashboard UI hardening:
- Repaired corrupted legacy `Home.tsx`.
- Sidebar login UX now provides actionable auth failure guidance (401/404/5xx/timeout).
- Streamlit supports session token input/login fallback and clearer auth-related API errors.

6. Audit script upgrades:
- `full_project_audit.py` now supports opt-in UI source inclusion while preserving heavy artifact exclusions.
- Added safe read-timeout and duplicate hashing guardrails for reliable report generation in this workspace.
- `training_data_audit.py` now includes full voice class set (including `fearful`), class balance, and speaker coverage summary.
- `training_gap_report.py` now includes pipeline contract checks + stale report detection + current-state recommendations.

## Reports Regenerated

- `reports/TRAINING_DATA.json`
- `reports/TRAINING_DATA.md`
- `reports/TRAINING_GAPS.json`
- `reports/TRAINING_GAPS.md`
- `reports/PROJECT_AUDIT.json`
- `reports/PROJECT_AUDIT.md`
- Baseline snapshot captured in `reports/BASELINE_2026-02-20_PRECHANGE.md`.

## Validation Evidence

- Backend/unit tests passed:
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/pytest -q tests/test_monitoring.py tests/api/v1/test_training.py tests/test_main_bootstrap.py`
  - Result: `15 passed`.

- Frontend compile/test tooling was attempted but blocked by long-running local TypeScript/Vitest processes in this environment (no terminal output completion). The new UI tests were added but execution remains pending in this workspace.

## Risk Notes

- `scripts/system_scorecard.py` strict integration run is not included in this snapshot because it requires a fully running backend stack in this environment.
- Existing unrelated user-local modification (`ui-web/README.md`) was intentionally left untouched.
