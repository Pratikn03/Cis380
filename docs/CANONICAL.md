# Canonical Sources of Truth

## Purpose
Define authoritative files to prevent documentation drift and conflicting instructions.

## Scope
Applies to all first-party docs and READMEs in root, `docs/`, `services/`, `ui-web/`, `scripts/`, `data/`, `benchmarks/`, and `infra/terraform/`.

## Run locally
```bash
python3 scripts/quality/docs_quality_check.py --mode fast --threshold 85
```

## Test and quality commands
```bash
python3 scripts/quality/docs_quality_check.py --mode full --threshold 95
```

## Ownership and canonical links
- Owner: Sentifargo Engineering
- Last verified: 2026-02-11
- Docs index: `README.md`
- Style guide: `STYLE_GUIDE.md`

## Canonical file map
### Repository level
- Onboarding and local run: `../README.md`
- Contribution policy: `../CONTRIBUTING.md`

### Documentation system
- Docs index: `README.md`
- Style and quality policy: `STYLE_GUIDE.md`
- README section schema: `README_SCHEMA.md`
- Manifest and ownership: `docs-manifest.yml`

### Runtime and API
- Python API entrypoint: `../app/main.py`
- Gateway app entrypoint: `../services/gateway-kotlin/src/main/kotlin/com/sentifargo/gateway/SentifargoGatewayApplication.kt`
- GraphQL schema: `../services/gateway-kotlin/src/main/resources/graphql/schema.graphqls`

### CI and deployment
- Quality gate workflow: `../.github/workflows/quality-gates.yml`
- Canonical frontend deploy workflow: `../.github/workflows/deploy-production.yml`
- Production deployment runbook: `PRODUCTION_DEPLOYMENT.md`

## Legacy policy
- `ui-web/frontend/` is compatibility-only, non-production, and not part of required CI.
- Validate the legacy frontend only when legacy files change or when explicitly requested.
- Suggested compatibility commands: `cd ui-web/frontend && npm run build:compat` and `cd ui-web/frontend && npm run test:compat`.
- Legacy docs must include explicit non-authoritative markers.
