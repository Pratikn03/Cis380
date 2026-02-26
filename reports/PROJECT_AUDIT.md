# Full Project Audit Report

- Root: `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2`
- Full scan: **False**
- UI sources included: **True**
- Duplicate hashing skipped: **True**
- Scan exclusions: `.cache, .git, .idea, .mypy_cache, .next, .pytest_cache, .venv, .vscode, __pycache__, artifacts, build, data, dist, experiments, logs, models, node_modules, notebooks, reports, runs, venv`
- Analysis exclusions: `.cache, .git, .idea, .mypy_cache, .next, .pytest_cache, .venv, .vscode, __pycache__, artifacts, build, data, dist, experiments, logs, models, node_modules, notebooks, reports, runs, venv`
- Scan started: `2026-02-20T12:17:18`
- Scan duration (s): **9.69**
- Files scanned: **6444**
- Python files (total): **456**
- Python files (analyzed): **456**
- Total size (bytes): **1298016666**

## Infra Files Found

- Requirements/pyproject files: 2
  - `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/requirements.txt`
  - `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/pyproject.toml`
- Docker files: 4
  - `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/Dockerfile`
  - `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/Dockerfile.production`
  - `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/docker-compose.yml`
  - `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/services/gateway-kotlin/Dockerfile`
- CI files: 5
  - `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/.github/workflows/ci-cd.yml`
  - `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/.github/workflows/deploy-production.yml`
  - `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/.github/workflows/quality-gates.yml`
  - `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/.github/workflows/scorecard.yml`
  - `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/.github/workflows/test.yml`

## Data / Artifacts Summary (file counts)

- `data/raw`: **5000** files
- `data/processed`: **5000** files
- `artifacts`: **8** files
- `runs`: **1486** files
- `models`: **115** files
- `configs`: **25** files
- `reports`: **315** files

## FastAPI Wiring

- include_router() found: **33**
- endpoints found: **107**

### include_router snippets (first 50)
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/main.py` → `include_router(chat.router)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/main.py` → `include_router(rag.router)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/main.py` → `include_router(recommend.router)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/main.py` → `include_router(behavior.router)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/main.py` → `include_router(fraud.router)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/main.py` → `include_router(cyber.router)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/main.py` → `include_router(vision.router)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/main.py` → `include_router(_health_router)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/main.py` → `include_router(_app_risk_router, prefix="/api", dependencies=[Depends(require_auth)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/main.py` → `include_router(_app_monitor_router, prefix="/api", dependencies=[Depends(require_auth)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/main.py` → `include_router(_app_voice_router, prefix="/api", dependencies=[Depends(require_auth)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/main.py` → `include_router(_app_rag_router, prefix="/api", dependencies=[Depends(require_auth)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/main.py` → `include_router(_app_dsa_rag_router, prefix="/api", dependencies=[Depends(require_auth)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/main.py` → `include_router(_app_dsa_algo_router, dependencies=[Depends(require_auth)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/main.py` → `include_router(_app_brand_router, dependencies=[Depends(require_auth)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/main.py` → `include_router(_app_object_router, dependencies=[Depends(require_auth)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/main.py` → `include_router(_app_stt_router, prefix="/api", dependencies=[Depends(require_auth)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/main.py` → `include_router(_app_tts_router, prefix="/api", dependencies=[Depends(require_auth)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/main.py` → `include_router(_app_vision_temporal_router, prefix="/api", dependencies=[Depends(require_auth)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/main.py` → `include_router(_api_v1_router)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/main.py` → `include_router(_app_internal_router, dependencies=[Depends(require_auth)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/v1/router.py` → `include_router(auth.router)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/v1/router.py` → `include_router(auth.admin_router)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/v1/router.py` → `include_router(auth.users_router)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/v1/router.py` → `include_router(jobs.router)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/v1/router.py` → `include_router(rag.router)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/v1/router.py` → `include_router(models.router)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/v1/router.py` → `include_router(datasets.router)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/v1/router.py` → `include_router(training.router)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/full_project_audit.py` → `include_router()`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/full_project_audit.py` → `include_router({r.expr})`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/main.py` → `include_router(health_router)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/main.py` → `include_router(monitoring_router)`

### endpoints (first 100)
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/main.py` → `app.GET` `/`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/main.py` → `app.POST` `/detect-anomalies`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/main.py` → `app.POST` `/analyze-audio`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/main.py` → `app.POST` `/analyze-text`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/main.py` → `app.POST` `/ask-pdf`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/main.py` → `app.POST` `/recommend`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/main.py` → `app.GET` `/api/health`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/main.py` → `app.GET` `/`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/core/health.py` → `router.GET` `/health`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/core/health.py` → `router.GET` `/health/live`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/core/health.py` → `router.GET` `/health/ready`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/core/health.py` → `router.GET` `/health/detailed`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/core/health.py` → `router.GET` `/metrics`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/core/health.py` → `router.GET` `/ready`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/api/routes/behavior.py` → `router.POST` `/logs`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/api/routes/vision.py` → `router.POST` `/train`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/api/routes/vision.py` → `router.POST` `/predict`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/api/routes/vision.py` → `router.POST` `/face_emotion/predict`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/api/routes/vision.py` → `router.POST` `/video/predict`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/api/routes/recommend.py` → `router.POST` `/explain`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/api/routes/recommend.py` → `router.POST` `/multimodal`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/api/routes/recommend.py` → `router.POST` `/clothes`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/api/routes/recommend.py` → `router.POST` `/topn`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/api/routes/chat.py` → `router.POST` `/multimodal`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/api/routes/chat.py` → `router.GET` `/stream`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/api/routes/rag.py` → `router.POST` `/query`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/internal.py` → `router.GET` `/health`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/internal.py` → `router.POST` `/risk/analyze`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/internal.py` → `router.POST` `/rag/query`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/cyber_timeline.py` → `router.GET` `/events`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/cyber_timeline.py` → `router.GET` `/patterns`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/cyber_timeline.py` → `router.GET` `/sources`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/cyber_timeline.py` → `router.GET` `/summary`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/monitor.py` → `router.POST` `/log`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/monitor.py` → `router.GET` `/summary`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/monitor.py` → `router.GET` `/drift`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/monitor.py` → `router.GET` `/risk_summary`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/monitor.py` → `router.GET` `/events`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/monitor.py` → `router.POST` `/baseline/build`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/health.py` → `router.GET` `/health`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/vision_temporal.py` → `router.POST` `/predict`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/tts.py` → `router.POST` `/speak`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/dsa_algorithms.py` → `router.POST` `/algorithms/lca`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/dsa_algorithms.py` → `router.POST` `/algorithms/segment-tree`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/dsa_algorithms.py` → `router.POST` `/algorithms/min-cost-max-flow`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/dsa_algorithms.py` → `router.POST` `/algorithms/segment-tree-min`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/dsa_algorithms.py` → `router.POST` `/algorithms/bfs`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/dsa_algorithms.py` → `router.POST` `/algorithms/dfs`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/dsa_algorithms.py` → `router.POST` `/algorithms/shortest-paths`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/dsa_algorithms.py` → `router.POST` `/algorithms/shortest-paths/bellman-ford`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/dsa_algorithms.py` → `router.POST` `/algorithms/shortest-paths/floyd-warshall`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/dsa_algorithms.py` → `router.POST` `/algorithms/shortest-paths/zero-one-bfs`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/dsa_algorithms.py` → `router.POST` `/algorithms/mst`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/dsa_algorithms.py` → `router.POST` `/algorithms/scc`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/dsa_algorithms.py` → `router.POST` `/algorithms/topological-sort`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/dsa_algorithms.py` → `router.POST` `/algorithms/trie`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/dsa_algorithms.py` → `router.POST` `/algorithms/dp`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/fraud.py` → `router.POST` `/fraud`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/dsa_rag.py` → `router.POST` `/ask`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/dsa_rag.py` → `router.POST` `/ingest`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/dsa_rag.py` → `router.POST` `/upload`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/voice.py` → `router.POST` `/emotion`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/chat.py` → `router.POST` `/chat`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/rag.py` → `router.POST` `/ingest`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/rag.py` → `router.POST` `/index`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/rag.py` → `router.POST` `/upload`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/rag.py` → `router.POST` `/ask`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/rag.py` → `router.POST` `/query`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/rag.py` → `router.GET` `/status`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/rag.py` → `router.DELETE` `/docs/{doc_id}`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/fusion.py` → `router.POST` `/analyze`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/risk.py` → `router.POST` `/risk/analyze`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/object_detection.py` → `router.POST` `/detect`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/object_detection.py` → `router.POST` `/visualize`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/brand.py` → `router.POST` `/predict`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/recommender.py` → `router.POST` `/recommend`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/recommender.py` → `router.POST` `/recommend/explain`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/recommender.py` → `router.POST` `/recommend/multimodal`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/stt.py` → `router.POST` `/transcribe`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/v1/auth.py` → `router.POST` `/login`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/v1/auth.py` → `router.POST` `/refresh`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/v1/auth.py` → `users_router.GET` `/me`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/v1/auth.py` → `admin_router.GET` `/users`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/v1/auth.py` → `admin_router.POST` `/users`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/v1/auth.py` → `admin_router.GET` `/roles`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/v1/auth.py` → `admin_router.POST` `/roles`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/v1/auth.py` → `admin_router.POST` `/bootstrap`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/v1/jobs.py` → `router.POST` `/start`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/v1/jobs.py` → `router.GET` `/{job_id}`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/v1/jobs.py` → `router.POST` `/{job_id}/cancel`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/v1/jobs.py` → `router.GET` `/{job_id}/logs`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/v1/rag.py` → `router.POST` `/upload`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/v1/rag.py` → `router.POST` `/index`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/v1/rag.py` → `router.POST` `/eval`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/v1/rag.py` → `router.POST` `/query`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/v1/training.py` → `router.GET` `/overview`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/v1/training.py` → `router.GET` `/domain/{domain}`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/truth_table_audit.py` → `router.GET` `/x`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/truth_table_audit.py` → `app.POST` `/y`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/api/health.py` → `router.GET` `/health`

## RAG-related Candidates (heuristic)

- Files flagged: **3**

- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/rag_dsa/online.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/rag_dsa/pipeline.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/full_project_audit.py`

## Training/Modeling Candidates (heuristic)

- Files flagged: **53**

- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/agent/train_brand_logo_detector.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/v1/training.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/core/config.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/agent/chat_responses.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/api/routes/vision.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/main.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/services/vision/yolov3.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/pages/metrics.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/download_kaggle_data.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/main.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/predict_yolo.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/experimental/train_behavior_v2.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/experimental/train_real_fake.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/experimental/train_voice_emotion_v2.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/full_project_audit.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/import_celeb_v2_vision.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/prepare_brand_data.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/prepare_intel_scene_vision.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/show_model_metrics.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/stt/train_whisper.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/train_all.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/train_all_vision.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/train_all_vision_full.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/train_brand_multiclass.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/train_production.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/training_data_audit.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/training_gap_report.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/vision/download_yolov3.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/vision/run_yolov3.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/voice/eval_emotion_ssl.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/voice/ssl_utils.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/voice/train_emotion_ssl.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/setup_dummy_data.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/train/train_brand_logo_detector.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/train/train_face_emotion.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/train/train_video_temporal.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/train/train_video_temporal_lstm.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/sequence/train_gru.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/sequence/train_lstm.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/sequence/transformer_tcn.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/supervised/train_cyber_supervised.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/supervised/train_fraud_supervised.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/vision/train_vision_model.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais_v/training/train_30seq.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais_v/training/train_30seq_torch.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais_v/training/train_nlp.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais_v/training/train_vision.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/vision/brand/data_utils.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/vision/brand/recognizer.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/tests/test_data_quality_scripts.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/train_recommender.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/train_yolo.py`

## Duplicate Files (identical hash; text/source files only, <= 524288 bytes)

- Groups: **0** (showing top 30)


## Python Compile Errors

- Errors: **0** (showing up to 50)


## Unreferenced Internal Modules (heuristic)

- Unreferenced: **191** (showing up to 100)

- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/agent/orchestrator.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/agent/train_brand_logo_detector.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/chatbot/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/chatbot/context_manager.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/chatbot/recommend_handler.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/core/logging.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/db/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/dsa_algorithms/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/fusion/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/agent/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/agent/orchestrator.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/agent/policy.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/agent/utils/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/agent/utils/shap_explainer.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/api/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/rag/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/rag/embed.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/rag/loader.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/rag/retriever.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/rag/service.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/mlops/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/monitoring/alerts.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/monitoring/latency.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/rag/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/rag_dsa/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/rag_dsa/build_index.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/services/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/services/alert_service.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/services/async_worker.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/services/vision/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/classic_chat.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/config.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/handlers/books.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/handlers/games.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/handlers/static_fallbacks.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/pages/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/pages/brand.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/pages/chat.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/pages/command_center.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/pages/live.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/pages/metrics.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/pages/risk.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/pages/tools.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/pages/voice_chat.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/risk_dashboard.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/ui/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/ui/theme.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/unified_chat.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/utils.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/vision_local/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/vision_local/detector.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/vision_local/index.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/workers/tasks.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/cli.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/orchestration/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/orchestration/behavior_flow.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/orchestration/cyber_flow.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/orchestration/fraud_flow.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/orchestration/fusion_flow.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/orchestration/nlp_flow.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/orchestration/vision_flow.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/pipeline/build_features.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/pipeline/ingest.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/pipeline/train_models.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/train/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/train/train_behavior.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/train/train_cyber.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/train/train_face_emotion.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/train/train_fraud.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/train/train_fusion.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/train/train_movielens_recommender.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/train/train_recommender.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/train/train_video_temporal.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/train/train_video_temporal_lstm.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/anomaly/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/anomaly/evaluate_anomaly.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/anomaly/train_autoencoder.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/anomaly/train_isolation_forest.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/anomaly/train_lof.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/anomaly/train_ocsvm.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/app/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/app/api_schema.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/app/predict_example.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/config/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/config/config_loader.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/drift/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/drift/drift_nlp.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/drift/drift_tabular.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/drift/drift_time_series.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/drift/drift_vision.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/ensembles/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/ensembles/blending.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/ensembles/stacking.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/evaluation/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/evaluation/evaluate_all.py`

## Notes

- Unreferenced internal modules found (may indicate duplicates/dead code).
- Data summary capped at 5000 files for: data/raw, data/processed

_Generated in 9.69s._
