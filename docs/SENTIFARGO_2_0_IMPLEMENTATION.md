# Sentifargo 2.0 Implementation (Phase 1 Foundation)

This document tracks the implemented migration foundation for Sentifargo 2.0.

## Implemented in this repo

### 1) Kotlin GraphQL gateway scaffold
- Path: `services/gateway-kotlin`
- Stack: Kotlin + Spring Boot + Spring GraphQL
- Endpoint: `/graphql` (queries/mutations/subscriptions)
- Implemented operations:
  - Queries: `viewer`, `systemHealth`, `jobs`, `job`, `models`, `datasets`, `ragStatus`
  - Mutations: `login`, `refreshToken`, `startJob`, `queryRag`, `runRisk`, `scoreFraud`, `scoreCyber`, `scoreBehavior`, `createUploadSession`, `finalizeUpload`
  - Subscriptions: `jobProgress`, `inferenceTrace`, `systemAlerts`
- Upload flow:
  - Pre-signed S3 upload URL via `createUploadSession`
  - Finalization validates object existence and trace emission via `finalizeUpload`
- Security hardening:
  - Resolver-level auth guard enforces token for all non-auth operations
  - Upload mutations require auth and input validation (tool/content-type/object-key)

### 2) Next.js dashboard migration to GraphQL
- Apollo Provider added and mounted in root layout
- GraphQL operations centralized in `ui-web/next/src/lib/gateway-graphql.ts`
- Frontend auth token helper + shell auth gate/logout added
- Pages migrated to GraphQL:
  - `/` dashboard
  - `/login`
  - `/jobs`
  - `/rag`
  - `/risk`
  - `/models`
  - `/datasets`
- New pages:
  - `/live-media` (pre-signed upload + trace subscription)
  - `/admin` (viewer + health snapshot)

### 3) FastAPI compatibility changes
- Added internal envelope router: `app/api/internal.py`
  - `/internal/health`
  - `/internal/risk/analyze`
  - `/internal/rag/query`
- Added legacy deprecation headers middleware in `app/main.py`
  - `Deprecation`
  - `Sunset` (90 days)
  - `Link: </graphql>; rel="successor-version"`

### 4) Infrastructure scaffolding
- Compose stack: `compose.sentifargo2.yml`
  - FastAPI service
  - Kotlin GraphQL gateway
  - Next.js app
  - Redis
  - Postgres (pgvector image)
- Terraform scaffold: `infra/terraform`
  - modules for network, ecs, rds, eventing, storage, observability
  - environment tfvars for `dev`, `staging`, `prod`
- CI extension:
  - Added Kotlin gateway test job in `.github/workflows/ci-cd.yml`

## Next implementation steps
1. Add schema-level RBAC directives and role guards in Kotlin gateway.
2. Implement durable subscription fan-out via EventBridge + SQS consumers (currently scaffold/in-memory).
3. Replace gateway proxy calls with private `/internal/*` calls for all domains.
4. Add GraphQL code generation in Next and update pages to generated typed hooks.
5. Add contract, integration, and e2e test suites for GraphQL + subscriptions.
6. Expand Terraform modules to production-grade security groups, IAM, ALB listeners, ECS task defs, and RDS hardening.
