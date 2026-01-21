# Sentifargo Full-System Audit Report

## Environment

```text
DATE: Wed Jan 21 07:51:07 CST 2026
PWD: /Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2
GIT: 2e1ce64
PYTHON: Python 3.13.5
NODE: v25.2.1
DOCKER: Docker version 28.5.1, build e180ab8
```

## Scoreboard

- **repo_hygiene**: FAIL
- **tests**: FAIL
- **api_health**: PASS
- **openapi**: PASS
- **metrics**: PASS
- **rag_query**: FAIL
- **next_build**: PASS
- **dvc**: PASS
- **reproducibility**: FAIL

## Key Evidence Paths

- Latest audit folder: `reports/audit_20260121_075107`
- Inspect these files for details:
  - `03_pytest.txt` (tests)
  - `05_health.json` / `05_openapi_head.txt` / `05_metrics_head.txt`
  - `07_rag_query.json`
  - `09_next_build.txt`
  - `11_dvc_status.txt`
