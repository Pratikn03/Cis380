# Legacy Code Documentation

## Overview

Sentifargo evolved from multiple iterations of the codebase. This document explains what's legacy, what's current, and the deprecation roadmap.

## Architecture Evolution

```
v0.1 (Original)     v0.2 (Refactored)     v1.0 (Current)
----------------    ------------------    ----------------
backend/            app/legacy/           app/
api/                app/legacy/api/       app/api/
agent/              app/legacy/agent/     app/services/
rag/                app/legacy/rag/       app/rag/
```

## Current vs Legacy Mapping

### ✅ Current (Preferred)

| Component | Location | Status |
|-----------|----------|--------|
| Main API | `app/main.py` | ✅ Active |
| Chat API | `app/api/routes/chat.py` | ✅ Active |
| RAG Service | `app/rag/` | ✅ Active |
| Streamlit UI | `app/streamlit_chatbot/` | ✅ Active |
| Monitoring | `app/monitoring/` | ✅ Active |
| ML Services | `app/services/` | ✅ Active |

### ⚠️ Legacy (Deprecated)

| Component | Location | Reason | Migration Path |
|-----------|----------|--------|----------------|
| Legacy API Routes | `app/legacy/api/routes/` | Older endpoint structure | Use `/api/*` routes |
| Legacy Orchestrator | `app/legacy/agent/orchestrator.py` | Type issues, tightly coupled | Use `app/services/` |
| Legacy RAG | `app/legacy/rag/` | Older vector store implementation | Use `app/rag/` |
| Legacy Chat Responses | `app/legacy/agent/chat_responses.py` | Hardcoded responses | Use orchestrator |

### 🗑️ Deprecated (To Remove)

| Component | Location | Target Removal |
|-----------|----------|----------------|
| Old backend | `backend/main.py` | v2.0 |
| Standalone API | `api/routes/` | v2.0 |
| Old agent | `agent/orchestrator.py` | v2.0 |

## Why Legacy Code Exists

### 1. Backwards Compatibility

The legacy routes (`app/legacy/api/routes/`) are still mounted in `app/main.py` for backwards compatibility:

```python
# app/main.py
from app.legacy.api.routes import behavior, chat, cyber, fraud, rag, recommend, vision

# Legacy routers (no authentication required for demo)
app.include_router(fraud.router, prefix="/api/fraud", tags=["fraud"])
app.include_router(cyber.router, prefix="/api/cyber", tags=["cyber"])
```

### 2. Demo/Testing

Some legacy endpoints are simpler and useful for quick testing without authentication.

### 3. Migration In Progress

Some components are being migrated incrementally:
- RAG: Legacy uses TF-IDF, current uses embeddings
- Chat: Legacy has hardcoded responses, current uses orchestrator

## Type Issues in Legacy Code

The legacy orchestrator has known type issues (reported by pyright/mypy):

```python
# app/legacy/agent/orchestrator.py
# Known issues:
# - Mixed DataFrame/ndarray handling
# - Optional fields not properly typed
# - Pipeline expects DataFrame but receives ndarray
```

**Workaround**: The current services (`app/services/`) have proper typing.

## Migration Guide

### For API Users

**Old (Legacy):**
```python
# Direct endpoint call
POST /api/fraud
{"features": [1.0, 2.0, ...]}
```

**New (Current):**
```python
# Through orchestrator
POST /api/chat
{"message": "analyze this transaction for fraud..."}

# Or through risk endpoint
POST /api/risk/analyze
{"features": {...}, "analysis_type": "fraud"}
```

### For Developers

1. **Don't add to legacy**: New features go in `app/` not `app/legacy/`
2. **Migrate when touching**: If you modify legacy code, consider migrating it
3. **Test both**: Ensure legacy routes still work for backwards compatibility

## Deprecation Timeline

| Phase | Date | Action |
|-------|------|--------|
| Phase 1 | Q1 2024 | Document legacy code (this file) |
| Phase 2 | Q2 2024 | Add deprecation warnings to legacy endpoints |
| Phase 3 | Q3 2024 | Default new users to current API |
| Phase 4 | Q4 2024 | Remove legacy routes (major version bump) |

## Files to Review Before Removal

Before removing legacy code, ensure these are migrated:

### Legacy Routes (`app/legacy/api/routes/`)

```
app/legacy/api/routes/
├── behavior.py      # → app/api/routes/behavior.py
├── chat.py          # → app/api/routes/chat.py (done)
├── cyber.py         # → app/api/routes/cyber.py
├── fraud.py         # → app/api/routes/fraud.py
├── rag.py           # → app/api/routes/rag.py (done)
├── recommend.py     # → app/api/routes/recommend.py (done)
└── vision.py        # → app/api/routes/vision.py (done)
```

### Legacy Agent (`app/legacy/agent/`)

```
app/legacy/agent/
├── orchestrator.py  # → app/services/orchestrator.py
├── chat_responses.py # → app/services/chat_responses.py
└── utils/
    └── shap_explainer.py # → src/anomaly/explainability/
```

### Legacy RAG (`app/legacy/rag/`)

```
app/legacy/rag/
├── service.py       # → app/rag/service.py (done)
└── vector_store/    # → app/rag/vector_store.py
```

## Testing Legacy vs Current

```bash
# Test legacy endpoints
pytest tests/legacy/ -v

# Test current endpoints
pytest tests/api/ -v

# Test both (default)
pytest tests/ -v
```

## Configuration

The legacy code can be disabled via environment variable:

```bash
# Disable legacy routes (for testing)
DISABLE_LEGACY_ROUTES=true uvicorn app.main:app
```

## Questions?

- **Why keep legacy?** Backwards compatibility for existing integrations
- **When to use legacy?** Only for migration testing or specific legacy features
- **How to migrate?** See migration guide above or ask in discussions

## Related Documentation

- [Architecture](ARCHITECTURE.md) - Current system architecture
- [API Reference](../README.md) - Current API and service overview
- [MLOps Roadmap](MLOPS_ROADMAP.md) - Future improvements
