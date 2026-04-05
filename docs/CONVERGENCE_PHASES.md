# Convergence Phases

## Purpose
Define the branch, commit, and ownership protocol for the canonical cutover from mixed legacy/canonical runtime to a single canonical production path.

## Branch Protocol
1. Create `snapshot/local-checkout-2026-04-05` from the current local checkout.
2. Commit the current meaningful repo state there, excluding transient outputs and generated temp files listed in the snapshot manifest.
3. Create `convergence/canonical-cutover-release-bar` from that snapshot commit.
4. Land the remaining topic commits on the convergence branch without squashing.

## Commit Protocol
1. `repo: snapshot local checkout and add convergence protocol`
2. `backend: remove default legacy runtime path and define canonical FastAPI boundary`
3. `readiness: normalize training and monitoring truth into canonical status inputs`
4. `frontend: enforce canonical JWT auth and align Next with gateway contract`
5. `quality: add release-bar aggregator and replace stale readiness truth`
6. `ops: harden production config and dependency validation`
7. `docs: retire legacy from canonical guidance and move legacy frontend to compatibility-only`

## Ownership
- Agent 1: repo root, `docs/`, `reports/`, `scripts/quality/`
- Agent 2: `app/main.py`, `app/core/*`, `app/api/v1/*`, `app/legacy/api/*`
- Agent 3: `app/monitoring/*`, `scripts/training_*`, `scripts/voice/*`, `reports/TRAINING_*`, `PROJECT_STATUS.md`
- Agent 4: `ui-web/next/src/lib/*`, `ui-web/next/src/components/auth/*`, `ui-web/next/src/app/login/*`, gateway client/schema alignment
- Agent 5: `scripts/quality/*`, `quality/waivers.yml`, `.github/workflows/quality-gates.yml`, `reports/RELEASE_BAR.*`
- Agent 6: `docker-compose.production.yml`, production validation, deploy/runtime docs, health/dependency checks
- Agent 7: `ui-web/frontend/**`, `docs/CANONICAL.md`, `docs/LEGACY.md`, `README.md`

## Integration Order
- Phase 0 first and alone.
- Backend boundary and readiness normalization can proceed in parallel once the snapshot branch exists.
- Frontend auth starts after the backend auth/runtime contract is explicit.
- Release-bar work consumes readiness outputs rather than defining a second readiness model.
- Production hardening starts after backend and frontend auth/runtime expectations are settled.
- Docs and legacy retirement land last so guidance reflects merged truth.

## Transient Exclusions
The snapshot branch excludes transient outputs and temp files from the baseline commit:
- `output/**`
- `ui-web/frontend/*.tsbuildinfo`
- `ui-web/frontend/*.timestamp-*`
- `ui-web/frontend/node_modules/**`
- `dataset/**/*.cache`
- any equivalent local logs, screenshots, or build-temp files recorded in the snapshot manifest

## Guardrails
- The snapshot branch is the archival baseline for the current local checkout.
- The convergence branch is the implementation branch for canonical cutover.
- Legacy code may remain in-repo temporarily, but it must not remain in the default runtime path or canonical release bar.
