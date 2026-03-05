# Live Stack Smoke Report (2026-03-05)

## Targets
- Frontend: `http://127.0.0.1:3000`
- Gateway: `http://127.0.0.1:8081`
- API: `http://127.0.0.1:8000`

## Readiness
- API `GET /health`: `200`
- API `GET /readyz`: `200`
- Gateway `GET /actuator/health`: `200`
- Gateway `/graphql` reachable
- Frontend `HEAD /`: `200`

## Desktop Routes
- `/`, `/rag`, `/live-media`, `/risk`, `/jobs`, `/models`, `/datasets`, `/admin`, `/settings`, `/login`: loaded with no crash overlay.

## Interaction Checks
- Risk:
  - `Run Fraud/Cyber/Behavior`: JSON result rendered.
  - `Run Fusion Risk`: JSON result rendered.
- RAG:
  - Queries returned answer payloads.
  - `chat/rag/movies` mode toggle controls were not present on current page build.
- Live Media:
  - File selection worked for `dataset/images/val/sample_0.jpg`.
  - `Upload + Finalize` produced inline `INTERNAL_ERROR` without UI crash.
- Jobs:
  - `Refresh` worked.
  - `Start RAG Index` entered `Starting...`; no new row observed in short wait.
- Models/Datasets:
  - Refresh actions worked.
  - Empty states rendered cleanly.

## Mobile Sanity (`390x844`)
- `/`, `/risk`, `/rag`, `/live-media`: loaded and remained navigable.

## Classification
- `fail_ui`: none observed.
- `soft_warning`: live-media backend internal error; jobs start not visible in table during short observation window.
