# UI Web Workspace

## Purpose
Define frontend application boundaries and identify the canonical production UI target.

## Scope
- Canonical production frontend: `ui-web/next`
- Legacy frontend (non-production): `ui-web/frontend`

## Run locally
### Next (canonical)
```bash
cd ui-web/next
npm install
npm run dev
```

### Legacy frontend (optional)
```bash
cd ui-web/frontend
npm install
npm run dev
```

## Test and quality commands
Run from repository root:
```bash
make quality-fast
make quality-test
make quality-docs-fast
```

## Ownership and canonical links
- Owner: Sentifargo Web Platform
- Last verified: 2026-02-11
- Canonical frontend README: `next/README.md`
- Canonical repository docs: `../docs/README.md`
