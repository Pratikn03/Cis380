# README Section Schema

## Purpose
Define a mandatory section contract for first-party `README.md` files.

## Scope
Applies to README files listed in `docs/docs-manifest.yml` with `requires_schema: true`.

## Required section order
All scoped README files must include the following headings in exact order:
1. `## Purpose`
2. `## Scope`
3. `## Run locally`
4. `## Test and quality commands`
5. `## Ownership and canonical links`

## Notes
- Additional sections are allowed **after** required sections.
- Required section names are case-sensitive.
- Missing or out-of-order required sections fail docs quality checks.

## Ownership and canonical links
- Owner: Sentifargo Engineering
- Last verified: 2026-02-11
- Canonical policy: `STYLE_GUIDE.md`
