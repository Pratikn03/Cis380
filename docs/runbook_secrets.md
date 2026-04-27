# Production secrets runbook

This runbook covers the **VPS + docker-compose** target. For dev, edit
`.env.local`; do not put real keys in `.env.development` (committed).

## What is a secret here

A secret is anything that, if leaked, lets someone impersonate the
service or escalate inside it. As of 2026-04 the production stack uses:

| Secret | Used by | File |
|---|---|---|
| `POSTGRES_PASSWORD` | postgres, api, worker, migrate | `secrets/postgres_password.txt` |
| `SECRET_KEY` | api (JWT signing) | `secrets/secret_key.txt` |
| `ANTHROPIC_API_KEY` | api (multi-agent planner/triage/synthesis) | `secrets/anthropic_api_key.txt` |
| `GRAFANA_PASSWORD` | grafana admin login | `secrets/grafana_password.txt` |

## Layout

The Caddy overlay (`docker-compose.caddy.yml`) maps each file in
`./secrets/` to `/run/secrets/<name>` inside the relevant containers and
sets `<NAME>_FILE=/run/secrets/<name>` so the application code can read
them via the `*_FILE` convention. Plain `<NAME>` env vars in `.env`
remain supported as a fallback for development.

```
secrets/
├── postgres_password.txt   # 0600 root:root
├── secret_key.txt          # 0600 root:root
├── anthropic_api_key.txt   # 0600 root:root
└── grafana_password.txt    # 0600 root:root
```

The `secrets/` directory **must be gitignored** (already covered by the
top-level `secrets/` rule — verify before committing the first time).

## Provisioning

On a fresh VPS:

```bash
sudo install -d -m 700 -o root -g root /opt/sentifargo/secrets
cd /opt/sentifargo
# Generate fresh values; never reuse across environments.
openssl rand -hex 32 | sudo tee secrets/postgres_password.txt > /dev/null
openssl rand -hex 32 | sudo tee secrets/secret_key.txt > /dev/null
openssl rand -hex 24 | sudo tee secrets/grafana_password.txt > /dev/null
echo "sk-ant-...your-key..."  | sudo tee secrets/anthropic_api_key.txt > /dev/null
sudo chmod 600 secrets/*.txt
```

The host `.env` (also `0600 root:root`) holds non-secret env: domain,
ACME email, ports, etc.:

```env
SENTIFARGO_DOMAIN=app.example.com
CADDY_ACME_EMAIL=ops@example.com
APP_ENV=production
LLM_MODE=auto
```

## Rotation

Rotation policy:

- `POSTGRES_PASSWORD` — every 90 days, or on operator turnover.
- `SECRET_KEY` — every 180 days, or after any suspected token leak.
  Rotation forces all sessions to invalidate.
- `ANTHROPIC_API_KEY` — every 90 days, or after a Claude console alert.
- `GRAFANA_PASSWORD` — every 180 days.

To rotate (zero-downtime where possible):

1. Write the new value to a temporary file (`*.new`):
   ```bash
   openssl rand -hex 32 | sudo tee secrets/secret_key.txt.new > /dev/null
   sudo chmod 600 secrets/secret_key.txt.new
   ```
2. Atomically replace the live file:
   ```bash
   sudo mv secrets/secret_key.txt.new secrets/secret_key.txt
   ```
3. Recreate the affected container (Docker re-mounts the secret on
   start; reload alone does not re-read file-backed secrets):
   ```bash
   docker compose -f docker-compose.production.yml -f docker-compose.caddy.yml \
       up -d --force-recreate api worker
   ```
4. For `POSTGRES_PASSWORD`, run the password change against a live
   Postgres before cycling:
   ```bash
   docker exec -it sentifargo-postgres psql -U sentifargo -d sentifargo \
       -c "ALTER USER sentifargo WITH PASSWORD '<new>';"
   ```
   Then update `secrets/postgres_password.txt` and restart `api` +
   `worker` + `migrate`.

## Backup and recovery

- Postgres dumps run nightly via `scripts/backup_postgres.sh`
  (cron 03:00 UTC). Default retention: 30 days under
  `/var/backups/sentifargo/postgres/`.
- The `secrets/` directory itself is **not** backed up by that script
  — copy it to the operator's password manager separately. Treat it
  the same way you treat SSH keys.
- Caddy ACME state lives in the `caddy-data` volume; back up via:
  ```bash
  docker run --rm -v sentifargo_caddy-data:/data -v $(pwd):/backup \
      alpine tar czf /backup/caddy-data-$(date +%F).tar.gz -C /data .
  ```

## Incident response

A leaked key is a P1 page:

1. Rotate the affected secret immediately following the steps above.
2. Revoke the old value in the upstream provider:
   - `ANTHROPIC_API_KEY`: Anthropic console → revoke.
   - JWTs minted with the old `SECRET_KEY` invalidate automatically once
     the API restarts; force users to re-login.
3. Open an incident in `incidents` table via the admin panel; tag with
   `secret_leak`.
4. Post-mortem within 5 business days.
