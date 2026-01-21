# Security

- JWT auth with access/refresh tokens under `/api/v1/auth/*`.
- RBAC enforced with `admin`, `analyst`, `viewer` roles.
- Upload allowlist + max size enforcement for documents.
- Prompt-injection detection + PII redaction in RAG pipeline.
- Audit logging stored in Postgres and `logs/audit/audit.jsonl`.

## Environment controls

- `AUTH_TOKEN` (legacy bearer token)
- `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`
- `CORS_ORIGINS` to control frontend access

## Runbook

Rotate tokens by updating `SECRET_KEY` and reissuing JWTs.
