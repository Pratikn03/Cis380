# Canonical Architecture (Tier-6)

## Entry points
- Primary API: `app/main.py`
- Primary UI: `app/streamlit_chatbot/app.py`
- Optional minimal deploy API: `deploy/api/main.py`
- React UI: `ui-web/frontend`

## Current vs Legacy
- Current API routes: `app/api/*` (preferred)
- Legacy routes: `app/legacy/api/routes/*` (compatibility only)

## Single source of truth
- API contract: `/openapi.json` (captured in `reports/openapi.json`)
- UI endpoint map must be centralized (target: one shared module for Streamlit + React)

## Tier-6 guarantees
- Contract diff check passes (UI routes exist in OpenAPI)
- E2E smoke tests pass
- Evaluation harness produces `reports/SYSTEM_SCORECARD.md`
- Claims evidence report present (`reports/CLAIM_EVIDENCE.md`)
- Truth table audit present (`reports/TRUTH_TABLE.md`)

## Tier-6 plan
- Add dashboards under `dashboards/`
- Add SLO report in `reports/`
- Wire system scorecard into CI nightly
