# Sentifargo Next Command Center

## Purpose
Provide the canonical production dashboard for Sentifargo using Next.js and GraphQL.

## Scope
- App Router pages under `ui-web/next/src/app`
- Apollo GraphQL client integration
- Subscription-capable UI flows

## Run locally
```bash
cd ui-web/next
npm install
npm run dev
```

Required environment (`ui-web/next/.env.local`):
```bash
NEXT_PUBLIC_GRAPHQL_HTTP=http://localhost:8081/graphql
NEXT_PUBLIC_GRAPHQL_WS=ws://localhost:8081/graphql
```

## Test and quality commands
```bash
cd ui-web/next
npm run lint
npm run test:ci
npm run test:coverage
```

## Ownership and canonical links
- Owner: Sentifargo Frontend Team
- Last verified: 2026-02-11
- Canonical repo overview: `../../README.md`
- Canonical docs index: `../../docs/README.md`
- Canonical style policy: `../../docs/STYLE_GUIDE.md`

## Route ownership
- `/` dashboard
- `/login`
- `/jobs`
- `/rag`
- `/risk`
- `/live-media`
- `/models`
- `/datasets`
- `/admin`
- `/settings`
