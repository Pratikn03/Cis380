# Worktree Snapshot 2026-04-05

## Baseline
- Branch at capture: `main`
- HEAD at capture: `138158d`
- Snapshot branch: `snapshot/local-checkout-2026-04-05`
- Convergence branch: `convergence/canonical-cutover-release-bar`

## Counts
- Staged paths: `13`
- Unstaged paths: `1090`
- Untracked paths: `26`

## Included in Snapshot Commit
- Meaningful repo code, config, docs, reports, dataset, and test changes across `app`, `src`, `scripts`, `ui-web`, `services`, `docs`, `reports`, `tests`, `configs`, `infra`, `deploy`, `quality`, and `.github`
- Meaningful untracked candidates such as new API files, MLOps scripts, gateway exception handling, and Next auth/runtime files

## Excluded as Transient
- `output/**`
- `ui-web/frontend/*.tsbuildinfo`
- `ui-web/frontend/*.timestamp-*`
- `ui-web/frontend/node_modules/**`
- `dataset/**/*.cache`
- equivalent local logs, screenshots, and temp build files

## Ownership Buckets
- `reports`: 250
- `app`: 185
- `dataset`: 128
- `src`: 104
- `scripts`: 88
- `ui-web/next`: 57
- `data`: 52
- `tests`: 36
- `ui-web/frontend`: 30
- `docs`: 27
- `infra`: 27
- `configs`: 25
- `services/gateway-kotlin`: 21

## Notes
- This snapshot is archival. It preserves the meaningful current local checkout before canonical convergence starts.
- Historical/advisory reports remain in the repo, but later phases will move release truth to a single canonical release bar.
