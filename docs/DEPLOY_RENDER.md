# Render Backend + GitHub Pages Frontend

This project hosts the FastAPI backend separately from the static UI. GitHub Pages only serves frontend assets, so the API must run elsewhere (Render, Fly, Railway, VPS).

## 1) Deploy the FastAPI backend on Render

1. Create a new **Web Service** from your repo.
2. **Build command**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Start command**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
4. **Environment variables** (minimum):
   - `APP_ENV=production`
   - `AUTH_TOKEN=your-secure-token`
   - `CORS_ORIGINS=https://<your-username>.github.io`
   - `DSA_ONLINE_MODE=false` (offline-first)
   - `OPENAI_API_KEY` (optional, only if you want online fallback)
5. Deploy and copy your Render service URL, e.g. `https://sentifargo.onrender.com`.

## 2) Build + deploy the React UI to GitHub Pages

From repo root:

```bash
cd ui-web/frontend
VITE_API_BASE=https://sentifargo.onrender.com \
VITE_BASE_PATH=/Cis380/ \
npm run build
```

Deploy `ui-web/frontend/dist/` to the `gh-pages` branch.

Notes:
- If you use a **custom domain** for GitHub Pages, set `VITE_BASE_PATH=./`.
- Keep `VITE_API_BASE` pointed at the backend URL (Render/Fly/Railway).

## 3) Local dev (optional)

```bash
uvicorn app.main:app --reload
cd ui-web/frontend
VITE_API_BASE=http://localhost:8000 npm run dev
```

## Common issue checklist

- CORS: make sure `CORS_ORIGINS` includes your GitHub Pages domain.
- API down: GitHub Pages is static; backend must be live.
- Base path: for `github.io/<repo>`, set `VITE_BASE_PATH=/repo/` at build time.
