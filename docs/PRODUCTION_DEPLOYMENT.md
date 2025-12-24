# Production Deployment

This guide describes how to run OmniChatX as a production-style service using the included Docker Compose stack.

The production stack is defined in `docker-compose.production.yml` and includes:
- `omnichatx-api` (FastAPI)
- `omnichatx-ui` (Streamlit)
- `redis` (optional cache/session store)
- optional: `prometheus` + `grafana` (profile `monitoring`)
- optional: `nginx` reverse proxy (profile `production`)

## Prerequisites
- Docker Engine + Docker Compose v2 (`docker compose version`)
- A `.env` file (start from `.env.production.example`)
- (Optional) TLS certificates if you enable the nginx profile

## 1) Configure Environment

Create `.env`:

```bash
cp .env.production.example .env
```

Minimum recommended settings:
- `AUTH_TOKEN` (enables bearer auth on `/api/*`)
- `CORS_ORIGINS` (comma-separated)
- `API_PORT`, `UI_PORT` (if you need non-default ports)

## 2) Deploy (Default Profile)

This starts API + UI + Redis:

```bash
docker compose -f docker-compose.production.yml up -d --build
docker compose -f docker-compose.production.yml ps
```

Health checks:
- API: `http://localhost:${API_PORT:-8000}/health`
- UI:  `http://localhost:${UI_PORT:-8501}`

## 3) Enable Monitoring (Optional)

Start Prometheus + Grafana:

```bash
docker compose -f docker-compose.production.yml --profile monitoring up -d
```

Defaults:
- Prometheus: `http://localhost:${PROMETHEUS_PORT:-9090}`
- Grafana: `http://localhost:${GRAFANA_PORT:-3000}` (credentials from `.env`)

## 4) Enable Nginx Reverse Proxy (Optional)

The nginx profile expects certificates under `deploy/nginx/ssl/`:

```bash
mkdir -p deploy/nginx/ssl
# copy your cert/key to:
#   deploy/nginx/ssl/cert.pem
#   deploy/nginx/ssl/key.pem
```

Start nginx (and monitoring if desired):

```bash
docker compose -f docker-compose.production.yml --profile production up -d
```

## Authentication (AUTH_TOKEN)

If `AUTH_TOKEN` is set, routes under `/api/*` require:

`Authorization: Bearer <AUTH_TOKEN>`

Example:

```bash
curl -s http://localhost:8000/api/chat \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello","user_id":"prod"}'
```

## Model Artifacts in Production

The production compose mounts:
- `./models` → `/app/models` (read-only)
- `./artifacts` → `/app/artifacts` (read-only)
- `./data` → `/app/data` (read-write; for logs, embeddings, and uploads)

If you enable features that require trained artifacts, ensure the corresponding files exist on the host:
- Brand/logo YOLO: `artifacts/brand/yolo_logo_det.pt`
- Face emotion: `models/vision/face_emotion/model.pt`
- Vision classifier: `models/vision/resnet/model.pt`

If you deploy from a git checkout, make sure LFS artifacts are actually present (not pointer files):
```bash
git lfs install
git lfs pull
```

When artifacts are missing, affected endpoints return `503` with instructions.

## Operations

Logs:
```bash
docker compose -f docker-compose.production.yml logs -f omnichatx-api
docker compose -f docker-compose.production.yml logs -f omnichatx-ui
```

Restart:
```bash
docker compose -f docker-compose.production.yml restart omnichatx-api
```

Stop (all profiles):
```bash
docker compose -f docker-compose.production.yml --profile monitoring --profile production down
```

## Deployment Script Wrapper

If you prefer a wrapper around compose commands:

```bash
./scripts/deploy.sh deploy                 # default profile
./scripts/deploy.sh deploy -p monitoring   # monitoring profile
./scripts/deploy.sh deploy -p production   # monitoring + nginx
```

## Troubleshooting

### “401 Missing bearer token”
- Set `AUTH_TOKEN` consistently in `.env` and in your client/UI environment.

### “503 … model not trained”
- Train the missing model (see `scripts/README.md`) and re-run the containers.

### UI can’t reach API
- Confirm the UI container uses `OMNICHATX_BACKEND=http://omnichatx-api:8000` (it does by default).
- Check `docker compose ps` and `docker compose logs omnichatx-api`.
