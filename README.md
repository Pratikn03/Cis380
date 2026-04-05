# Sentifargo

## Purpose
Sentifargo is a multimodal risk-intelligence platform for fraud, cyber, behavior, RAG, and media workflows.

## Scope
- Canonical frontend: `ui-web/next` (Next.js + GraphQL)
- Canonical gateway: `services/gateway-kotlin` (Kotlin + Spring GraphQL)
- ML and API runtime: Python services under `app/` and `src/`
- Legacy frontend compatibility surface: `ui-web/frontend` (rollback/reference only; non-production; not required CI)

## Run locally
1. Start Python API:
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-ci.txt
uvicorn app.main:app --reload --port 8000
```
2. Start GraphQL gateway:
```bash
cd services/gateway-kotlin
export JAVA_HOME=/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home
export PATH="$JAVA_HOME/bin:$PATH"
export SENTIFARGO_FASTAPI_BASE_URL=http://localhost:8000
./gradlew bootRun
```
3. Start Next frontend:
```bash
cd ui-web/next
npm install
npm run dev
```

## Test and quality commands
Run from repo root:
```bash
make quality-fast
make quality-data
make quality-test
make quality-all
make quality-docs-fast
make quality-docs
```

## Ownership and canonical links
- Owner: Sentifargo Engineering
- Last verified: 2026-02-11
- Canonical docs index: `docs/README.md`
- Canonical mapping: `docs/CANONICAL.md`
- Documentation standards: `docs/STYLE_GUIDE.md`

## Related links
- Canonical frontend deploy workflow: `.github/workflows/deploy-production.yml`
- Quality gate workflow: `.github/workflows/quality-gates.yml`
- Terraform scaffold docs: `infra/terraform/README.md`

## License
MIT. See `LICENSE`.
