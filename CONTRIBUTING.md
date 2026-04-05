# Contributing to Sentifargo

Thanks for contributing. This guide keeps changes consistent, reviewable, and production-safe.

## Development setup
1. Create Python environment and install dependencies:
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-ci.txt
```
2. Optional frontend setup:
```bash
cd ui-web/next && npm install
cd ../frontend && npm install
```
3. Optional gateway setup:
```bash
cd services/gateway-kotlin
export JAVA_HOME=/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home
export PATH="$JAVA_HOME/bin:$PATH"
./gradlew --version
```

## Branch and PR rules
- Use small, focused PRs.
- Include tests for behavior changes.
- Update docs in the same PR when interfaces/workflows change.
- Do not commit generated/vendor artifacts (`node_modules`, caches, build outputs).

## Required local checks
Run from repository root:
```bash
make quality-fast
make quality-data
make quality-test
```
If changes are broad, run:
```bash
make quality-all
```

## Docs consistency requirements
- Follow `docs/STYLE_GUIDE.md`.
- Update `README.md` and/or `docs/README.md` when adding new modules or workflows.
- Mark legacy paths clearly as legacy.

## Commit message guidance
Use clear, action-oriented messages:
- `docs: unify README and docs index`
- `test: add gateway resolver coverage`
- `ci: enforce module-level quality gates`

## Reporting issues
Include:
1. Expected behavior
2. Actual behavior
3. Reproduction steps
4. Logs/errors
5. Relevant environment details (OS, Python, Node, Java)

## Ownership and canonical links
- Owner: Sentifargo Engineering
- Last verified: 2026-02-11
- Canonical docs index: `docs/README.md`
- Style policy: `docs/STYLE_GUIDE.md`
