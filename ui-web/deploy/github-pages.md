# GitHub Pages Deployment (Next.js Command Center)

Production deployment uses a single GitHub Actions workflow:
- `.github/workflows/deploy-production.yml`

## Runtime Prerequisites
- Backend hosted separately and publicly reachable.
- GitHub repository has Pages enabled for `GitHub Actions`.

## Required GitHub Repository Variables
- `NEXT_PUBLIC_GRAPHQL_HTTP` (for example `https://api.example.com/graphql`)
- `NEXT_PUBLIC_GRAPHQL_WS` (for example `wss://api.example.com/graphql`)

## Local Production Build Check
```bash
cd ui-web/next
npm install
STATIC_EXPORT=true NEXT_PUBLIC_BASE_PATH=/Cis380 npm run build
```

This generates static output in `ui-web/next/out`.

## Deployment Trigger
- Push to `main` with changes under `ui-web/next/**`, or
- manually run the `Deploy Production Frontend (Next.js)` workflow from the Actions tab.

## Notes
- `NEXT_PUBLIC_BASE_PATH` must match your repository Pages path (`/Cis380` in this repository).
- Legacy Vite frontend deploy scripts and workflow are intentionally removed.
