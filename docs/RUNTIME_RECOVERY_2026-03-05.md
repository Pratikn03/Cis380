# Runtime Recovery Notes (2026-03-05)

## Initial Problems
- Local stack repeatedly down on `3000`, `8081`, and `8000`.
- API startup perceived as hung due very slow import/startup path.
- Local DB env could point to Docker-only hostnames and block local standalone boot.
- Playwright MCP launch failed with Chrome profile lock (`Opening in existing browser session`).
- Many lingering exec processes created noisy runtime state.

## Recovery Performed
- Verified and restored readiness gates:
  - API `GET /health`, `GET /readyz`
  - Gateway `GET /actuator/health`, `/graphql` reachability
  - Frontend `HEAD /`
- Cleared stale Git/runtime helper processes.
- Cleared Playwright MCP Chrome profile lock state in `~/Library/Caches/ms-playwright/mcp-chrome`.
- Re-ran route and interaction smoke pass against the live local stack.

## Code-Level Stabilization in This Cycle
- Lazy-loaded heavyweight auth/core/service imports to reduce startup side effects.
- Added dev-safe DB URL fallback for Docker hostname values.
- Hardened fraud/risk runtime behavior with deterministic low-latency scoring.
- Switched RAG default embedder path to lightweight hashing for local reliability.

## Current Status
- Canonical local stack reachable during validation window.
- Route smoke pass completed without client runtime crashes.
- Remaining issues observed were backend degradations, not frontend crash defects.
