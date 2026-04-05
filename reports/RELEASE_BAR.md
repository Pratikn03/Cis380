# Release Bar

- Generated: 2026-04-05T19:42:23.051197+00:00
- Release ready: False
- Blocking pillars: runtime_smoke, production_blockers
- Warning pillars: artifact_readiness, docs_quality

## Pillars

| Pillar | Status | Blocking | Freshness (h) | Evidence |
| --- | --- | --- | --- | --- |
| auth_contract | pass | False | 0.3 | /Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/ui-web/next/src/lib/runtime.ts, /Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/ui-web/next/src/app/login/page.tsx, /Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/ui-web/next/src/components/auth/AuthProvider.tsx, /Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/main.py |
| code_quality | pass | False | 0.0 | quality/waivers.yml |
| artifact_readiness | warning | False | 1717.1 | /Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/reports/ARTIFACT_GATE.json |
| training_data_readiness | pass | False | 0.3 | /Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/reports/TRAINING_DATA.json |
| runtime_smoke | blocking | True | 763.7 | /Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/reports/LIVE_STACK_SMOKE_2026-03-05.md |
| docs_quality | warning | False | 1219.7 | /Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/reports/docs_scorecard.json |
| production_blockers | blocking | True | 0.3 | /Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/docs/PRODUCTION_READINESS_PLAN.md |

## Notes

- `auth_contract` generated_at: 2026-04-05T19:21:39.051823+00:00
- `code_quality` generated_at: 2026-04-05T19:41:41.867110+00:00
- `artifact_readiness` generated_at: 2026-01-24T06:35:09.717357+00:00
- `training_data_readiness` generated_at: 2026-04-05T19:25:13+00:00
- `runtime_smoke` generated_at: 2026-03-05T00:00:00+00:00
- `docs_quality` generated_at: 2026-02-14T00:00:00+00:00
- `production_blockers` generated_at: 2026-04-05T19:23:01.022328+00:00
