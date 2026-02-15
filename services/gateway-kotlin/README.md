# Sentifargo GraphQL Gateway (Kotlin)

## Purpose
Expose the GraphQL API and subscription gateway for Sentifargo while orchestrating Python backend services.

## Scope
- GraphQL endpoint (`/graphql`)
- GraphQL subscriptions (`jobProgress`, `inferenceTrace`, `systemAlerts`)
- Upload session and finalize orchestration
- Proxy/resolver integration with Python services

## Run locally
```bash
cd services/gateway-kotlin
export JAVA_HOME=/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home
export PATH="$JAVA_HOME/bin:$PATH"
export SENTIFARGO_FASTAPI_BASE_URL=http://localhost:8000
export SENTIFARGO_UPLOAD_BUCKET=sentifargo-uploads-local
export SENTIFARGO_UPLOAD_REGION=us-east-1
./gradlew bootRun
```

## Test and quality commands
```bash
cd services/gateway-kotlin
./gradlew --version
./gradlew clean test
./gradlew clean build
./gradlew jacocoTestReport jacocoTestCoverageVerification
```

## Ownership and canonical links
- Owner: Sentifargo Platform Team
- Last verified: 2026-02-11
- Canonical repo overview: `../../README.md`
- Canonical docs index: `../../docs/README.md`
- Canonical schema: `src/main/resources/graphql/schema.graphqls`

## Key environment variables
- `SENTIFARGO_FASTAPI_BASE_URL`
- `SENTIFARGO_FASTAPI_TIMEOUT_SECONDS`
- `SENTIFARGO_UPLOAD_BUCKET`
- `SENTIFARGO_UPLOAD_REGION`
- `SENTIFARGO_UPLOAD_SIGNED_URL_MINUTES`
- `SENTIFARGO_UPLOAD_MAX_BYTES`
