# Documentation Style Guide

## Purpose
Set enforceable writing and structure standards for all Sentifargo documentation.

## Scope
Applies to first-party markdown in root, `docs/`, `services/`, `ui-web/`, `scripts/`, `data/`, `benchmarks/`, and `infra/terraform/`.

## Run locally
```bash
make quality-docs-fast
make quality-docs
```

## Test and quality commands
```bash
make quality-docs-fast
make quality-docs
# Direct commands (CI parity):
python3 scripts/quality/docs_quality_check.py --mode full --threshold 95 --manifest docs/docs-manifest.yml
npx --yes markdownlint-cli@0.40.0 README.md docs/**/*.md ui-web/**/*.md services/**/*.md scripts/**/*.md data/**/*.md benchmarks/**/*.md infra/terraform/**/*.md --config .markdownlint.yml
vale README.md docs ui-web services scripts data benchmarks infra/terraform
```

## Ownership and canonical links
- Owner: Sentifargo Engineering
- Last verified: 2026-02-11
- Canonical map: `CANONICAL.md`
- README schema: `README_SCHEMA.md`

## Required README section order
All first-party `README.md` files must include these headings in this exact order:
1. `## Purpose`
2. `## Scope`
3. `## Run locally`
4. `## Test and quality commands`
5. `## Ownership and canonical links`

## Writing standards
- Use short, direct sentences.
- Use present tense and active voice.
- Use repository-relative paths.
- Keep command examples copy/paste safe.
- Avoid duplicate sections and contradictory instructions.

## Formatting standards
- Use sentence-case headings.
- Prefer numbered lists for step-by-step workflows.
- Use fenced code blocks with language labels.
- Keep heading depth shallow (`##` / `###`).

## Change-management requirements
Update docs in the same PR when changing:
- API interfaces, GraphQL schema, or endpoint behavior.
- CI workflows, quality thresholds, or deployment path.
- Required environment variables or run commands.

## Quality gates policy
Documentation is blocking when checks fail for:
- Missing required README sections.
- Broken internal links.
- Missing owner/last-verified metadata on canonical docs.
- Duplicate top-level sections in canonical docs.
