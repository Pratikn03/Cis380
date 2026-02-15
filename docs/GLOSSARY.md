# Glossary

## Purpose
Provide consistent definitions for platform terminology used across Sentifargo documentation.

## Scope
Terms in this glossary are authoritative for technical docs, READMEs, and status reports.

## Core terms
- **Sentifargo**: The overall multimodal risk-intelligence platform.
- **Gateway**: Kotlin Spring GraphQL service in `services/gateway-kotlin`.
- **Canonical frontend**: Next.js app in `ui-web/next` used for production deployment.
- **Legacy frontend**: Vite app in `ui-web/frontend` retained for compatibility and stabilization only.
- **RAG**: Retrieval-augmented generation flow using indexed documents and retrieval metadata.
- **DSA RAG**: Domain-specific retrieval flow for data-structure and algorithm knowledge sources.
- **Fusion risk**: Combined decision signal from fraud, cyber, and behavior model outputs.
- **Inference trace**: Ordered streaming events that describe model/runtime processing steps.
- **Quality gates**: Blocking CI checks for tests, coverage, data validation, and documentation quality.
- **Waiver**: Time-boxed, owner-attributed temporary threshold override in `quality/waivers.yml`.

## Ownership and canonical links
- Owner: Sentifargo Engineering
- Last verified: 2026-02-11
- Canonical docs index: `README.md`
- Canonical source map: `CANONICAL.md`
