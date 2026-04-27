# legacy/

Files here are preserved for reference but are **not** part of the canonical runtime.

| File | What it was | Replacement |
|---|---|---|
| `main_root_api.py` | Standalone FastAPI app on `:8001` (subset of routes, predates the `app/` package). | `app.main:app` on `:8000` (full router stack). |
| `streamlit_root.py` | Top-level Streamlit dashboard. | `ui-web/frontend/` (Vite + React). |

Canonical runtime entrypoints:

- **API**: `uvicorn app.main:app --host 0.0.0.0 --port 8000` (see `Makefile` `make dev`).
- **Web**: `cd ui-web/frontend && npm run dev` (Vite, port 5173).

Do not import from this directory in new code.
