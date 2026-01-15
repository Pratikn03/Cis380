# GitHub Pages Deployment (Sentifargo Command Center)

## Prerequisites
- Backend hosted separately (FastAPI is not deployable on GitHub Pages).
- `VITE_API_BASE` points to your backend URL.

## Build Steps
1) Install dependencies:
```
cd ui-web/frontend
npm install
```

2) Build with a base path (replace REPO_NAME with your GitHub repo name):
```
VITE_BASE_PATH=/REPO_NAME/ npm run build
```

3) Deploy `dist/` to GitHub Pages:
- Option A: Push `dist/` to a `gh-pages` branch.
- Option B: Configure a GitHub Actions workflow to publish `dist/`.

## Notes
- If you use a custom domain, set `VITE_BASE_PATH=/`.
- The backend must be reachable from the browser (public URL, not localhost).
