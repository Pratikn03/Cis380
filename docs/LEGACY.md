# Legacy and Compatibility Surface

## Overview

This document records code that is preserved for rollback, reference, and compatibility testing. Nothing in this file is the canonical product surface.

## Canonical vs Compatibility

### Canonical

| Component | Location | Status |
|-----------|----------|--------|
| Main frontend | `ui-web/next/` | Canonical |
| Gateway | `services/gateway-kotlin/` | Canonical |
| FastAPI runtime | `app/` and `src/` | Canonical |
| Main API entrypoint | `app/main.py` | Canonical |
| Current services | `app/services/` | Canonical |
| Current RAG | `app/rag/` | Canonical |

### Compatibility-only

| Component | Location | Use | Validation |
|-----------|----------|-----|------------|
| Legacy frontend | `ui-web/frontend/` | Rollback/reference UI and historical preview surface | `npm run build:compat` or `npm run test:compat` only when legacy files change or when explicitly requested |
| Legacy API routes | `app/legacy/api/routes/` | Historical endpoint compatibility | Keep only while deprecating older integrations |
| Legacy agent and RAG code | `app/legacy/agent/`, `app/legacy/rag/` | Historical reference for migrations | Do not extend for new work |

### Retired

| Component | Location | Target |
|-----------|----------|--------|
| Old backend path | `backend/` | Historical only |
| Standalone API path | `api/routes/` | Historical only |
| Old agent path | `agent/orchestrator.py` | Historical only |

## Policy

1. New canonical work goes in `app/`, `src/`, `services/gateway-kotlin/`, or `ui-web/next/`.
2. Legacy frontend work stays compatibility-only and should not be treated as a production deliverable.
3. Legacy validation is opt-in: run it only when touching legacy files or when explicitly requested.
4. Canonical release readiness should not depend on legacy frontend jobs.

## Compatibility Notes

- The legacy frontend remains in the repository for rollback and reference.
- Its build artifacts, tests, and deployment previews are not part of the canonical product path.
- If you need to validate it, prefer:

```bash
cd ui-web/frontend
npm run build:compat
npm run test:compat
```

## Related Documentation

- [Architecture](ARCHITECTURE.md) - Canonical system architecture
- [API Reference](../README.md) - Canonical API and service overview
- [MLOps Roadmap](MLOPS_ROADMAP.md) - Historical planning context
