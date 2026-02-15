# Render Backend + GitHub Pages Frontend (Next.js)

This project hosts the backend separately from the static UI.  
GitHub Pages serves the canonical Next frontend (`ui-web/next`) and the API runs elsewhere (Render, Fly, Railway, VPS, or ECS).

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

## 2) Build + deploy the Next UI to GitHub Pages

Production deploy is handled by GitHub Actions:

- Workflow: `.github/workflows/deploy-production.yml`
- App path: `ui-web/next`
- Artifact path: `ui-web/next/out`

Required repository variables:

- `NEXT_PUBLIC_GRAPHQL_HTTP` (for example `https://api.example.com/graphql`)
- `NEXT_PUBLIC_GRAPHQL_WS` (for example `wss://api.example.com/graphql`)

Local production build check:

```bash
cd ui-web/next
npm install
STATIC_EXPORT=true NEXT_PUBLIC_BASE_PATH=/Cis380 npm run build
```

Notes:
- `NEXT_PUBLIC_BASE_PATH` must match the repo Pages path (for this repo: `/Cis380`).
- Legacy Vite frontend (`ui-web/frontend`) is non-production and not part of release deploys.

## 3) Local dev (optional)

```bash
uvicorn app.main:app --reload --port 8000

cd services/gateway-kotlin
export SENTIFARGO_FASTAPI_BASE_URL=http://localhost:8000
./gradlew bootRun

cd ui-web/next
NEXT_PUBLIC_GRAPHQL_HTTP=http://localhost:8081/graphql \
NEXT_PUBLIC_GRAPHQL_WS=ws://localhost:8081/graphql \
npm run dev
```

## Common issue checklist

- CORS: ensure backend CORS allows your GitHub Pages domain.
- API down: GitHub Pages is static; backend/gateway must be live.
- Base path: for `github.io/<repo>`, ensure `NEXT_PUBLIC_BASE_PATH=/repo`.
- GraphQL vars: make sure `NEXT_PUBLIC_GRAPHQL_HTTP` and `NEXT_PUBLIC_GRAPHQL_WS` are set in repo variables.
