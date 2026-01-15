# Full Project Audit Report

- Root: `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2`
- Full scan: **False**
- Scan exclusions: `.cache, .git, .idea, .mypy_cache, .next, .pytest_cache, .venv, .vscode, __pycache__, artifacts, build, data, dist, experiments, logs, models, node_modules, notebooks, reports, runs, ui-web, venv`
- Analysis exclusions: `.cache, .git, .idea, .mypy_cache, .next, .pytest_cache, .venv, .vscode, __pycache__, artifacts, build, data, dist, experiments, logs, models, node_modules, notebooks, reports, runs, ui-web, venv`
- Scan started: `2026-01-14T22:01:29`
- Scan duration (s): **0.82**
- Files scanned: **499**
- Python files (total): **339**
- Python files (analyzed): **339**
- Total size (bytes): **31008656**

## Infra Files Found

- Requirements/pyproject files: 2
  - `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/requirements.txt`
  - `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/pyproject.toml`
- Docker files: 3
  - `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/Dockerfile`
  - `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/Dockerfile.production`
  - `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/docker-compose.yml`
- CI files: 3
  - `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/.github/workflows/ci-cd.yml`
  - `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/.github/workflows/ci.yml`
  - `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/.github/workflows/deploy-pages.yml`

## Data / Artifacts Summary (file counts)

- `data/raw`: **5000** files
- `data/processed`: **5000** files
- `artifacts`: **4** files
- `runs`: **3727** files
- `models`: **91** files
- `configs`: **18** files
- `reports`: **36** files

## FastAPI Wiring

- include_router() found: **19**
- endpoints found: **57**

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
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/main.py` → `include_router(_app_brand_router, dependencies=[Depends(require_auth)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/main.py` → `include_router(_app_stt_router, prefix="/api", dependencies=[Depends(require_auth)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/main.py` → `include_router(_app_tts_router, prefix="/api", dependencies=[Depends(require_auth)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/main.py` → `include_router(_app_vision_temporal_router, prefix="/api", dependencies=[Depends(require_auth)`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/full_project_audit.py` → `include_router()`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/full_project_audit.py` → `include_router({r.expr})`

### endpoints (first 100)
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
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/fraud.py` → `router.POST` `/fraud`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/dsa_rag.py` → `router.POST` `/ask`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/dsa_rag.py` → `router.POST` `/ingest`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/dsa_rag.py` → `router.POST` `/upload`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/voice.py` → `router.POST` `/emotion`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/chat.py` → `router.POST` `/chat`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/rag.py` → `router.POST` `/ingest`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/rag.py` → `router.POST` `/upload`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/fusion.py` → `router.POST` `/analyze`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/risk.py` → `router.POST` `/risk/analyze`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/brand.py` → `router.POST` `/predict`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/recommender.py` → `router.POST` `/recommend`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/recommender.py` → `router.POST` `/recommend/explain`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/recommender.py` → `router.POST` `/recommend/multimodal`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/stt.py` → `router.POST` `/transcribe`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/deploy/api/main.py` → `app.GET` `/`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/deploy/api/main.py` → `app.GET` `/health`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/deploy/api/main.py` → `app.POST` `/predict_fraud`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/deploy/api/main.py` → `app.POST` `/predict_cyber`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/deploy/api/main.py` → `app.POST` `/predict_fusion`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/deploy/api/main.py` → `app.POST` `/predict_nlp`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/deploy/api/main.py` → `app.POST` `/predict_vision`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/truth_table_audit.py` → `router.GET` `/x`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/truth_table_audit.py` → `app.POST` `/y`

## RAG-related Candidates (heuristic)

- Files flagged: **3**

- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/rag_dsa/online.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/rag_dsa/pipeline.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/full_project_audit.py`

## Training/Modeling Candidates (heuristic)

- Files flagged: **33**

- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/core/config.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/agent/chat_responses.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/api/routes/vision.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/main.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/pages/metrics.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/dashboard/components/shap_viz.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/experimental/train_behavior_v2.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/experimental/train_real_fake.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/experimental/train_voice_emotion_v2.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/full_project_audit.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/import_celeb_v2_vision.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/prepare_brand_data.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/prepare_intel_scene_vision.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/train_all.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/train_all_vision.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/train_all_vision_full.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/train_production.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/scripts/training_data_audit.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/train/train_brand_logo_detector.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/train/train_face_emotion.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/train/train_video_temporal.py`
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

## Duplicate Files (identical hash; <=2MB)

- Groups: **9** (showing top 30)

### sha256 `19454d5445271ec7a06a084f2b708072ebc8749c38a792598765672286f9ad5c` (6 files)
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/mlruns/497119083612192240/8baaac1d4fe6470da9fddcabcff2703c/metrics/accuracy`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/mlruns/497119083612192240/8baaac1d4fe6470da9fddcabcff2703c/metrics/f1`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/mlruns/497119083612192240/8baaac1d4fe6470da9fddcabcff2703c/metrics/pr_auc`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/mlruns/497119083612192240/8baaac1d4fe6470da9fddcabcff2703c/metrics/precision`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/mlruns/497119083612192240/8baaac1d4fe6470da9fddcabcff2703c/metrics/recall`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/mlruns/497119083612192240/8baaac1d4fe6470da9fddcabcff2703c/metrics/roc_auc`

### sha256 `af9554b330e69850bbf0dd095a2f575e8d59911b8cd2298b2faef6553c5b53b4` (6 files)
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais_v/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais_v/cli/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais_v/evaluation/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais_v/features/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais_v/training/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais_v/utils/__init__.py`

### sha256 `192f0012c3ba0a005d643fd0e6bd4e1d8db7cca0af5b32e1830b98cecf5469b2` (5 files)
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/mlruns/497119083612192240/2e8138b35e464c8aa2ddc0e74506b031/tags/mlflow.user`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/mlruns/497119083612192240/2fbf0cfe6386488dae65ac945f546ac5/tags/mlflow.user`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/mlruns/497119083612192240/77c133a832264a8a9c681c41a3e96d07/tags/mlflow.user`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/mlruns/497119083612192240/8baaac1d4fe6470da9fddcabcff2703c/tags/mlflow.user`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/mlruns/497119083612192240/ae201b6ab42042d9a4b41024e0923e0d/tags/mlflow.user`

### sha256 `646c19373ac9e27e972c8e3bdf6554c4c10d23006c1abec3407cbff80c4ab71f` (5 files)
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/mlruns/497119083612192240/2e8138b35e464c8aa2ddc0e74506b031/tags/mlflow.source.type`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/mlruns/497119083612192240/2fbf0cfe6386488dae65ac945f546ac5/tags/mlflow.source.type`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/mlruns/497119083612192240/77c133a832264a8a9c681c41a3e96d07/tags/mlflow.source.type`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/mlruns/497119083612192240/8baaac1d4fe6470da9fddcabcff2703c/tags/mlflow.source.type`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/mlruns/497119083612192240/ae201b6ab42042d9a4b41024e0923e0d/tags/mlflow.source.type`

### sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (5 files)
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/dashboards/.gitkeep`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/generative/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/nlp/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/vision/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/tests/contract/.gitkeep`

### sha256 `eea8d43a676a6a702f4a711d1a671b74015e45d65907d8ec497e7b99a1614990` (5 files)
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/mlruns/497119083612192240/2e8138b35e464c8aa2ddc0e74506b031/tags/mlflow.source.git.commit`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/mlruns/497119083612192240/2fbf0cfe6386488dae65ac945f546ac5/tags/mlflow.source.git.commit`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/mlruns/497119083612192240/77c133a832264a8a9c681c41a3e96d07/tags/mlflow.source.git.commit`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/mlruns/497119083612192240/8baaac1d4fe6470da9fddcabcff2703c/tags/mlflow.source.git.commit`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/mlruns/497119083612192240/ae201b6ab42042d9a4b41024e0923e0d/tags/mlflow.source.git.commit`

### sha256 `831f5698f107d1f36449596d3603e9667ee7ed59d9ff8ff45b2be965b580e0d8` (3 files)
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/mlruns/497119083612192240/2fbf0cfe6386488dae65ac945f546ac5/tags/mlflow.runName`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/mlruns/497119083612192240/77c133a832264a8a9c681c41a3e96d07/tags/mlflow.runName`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/mlruns/497119083612192240/ae201b6ab42042d9a4b41024e0923e0d/tags/mlflow.runName`

### sha256 `cc113b45459ea17bee7ed876a9f5332f93524119cf58aab8ef4d36c9e2ff5d99` (3 files)
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/mlruns/497119083612192240/2fbf0cfe6386488dae65ac945f546ac5/tags/mlflow.source.name`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/mlruns/497119083612192240/77c133a832264a8a9c681c41a3e96d07/tags/mlflow.source.name`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/mlruns/497119083612192240/ae201b6ab42042d9a4b41024e0923e0d/tags/mlflow.source.name`

### sha256 `01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b` (2 files)
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/rag/vector_store/.gitkeep`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/universal_anomaly_intelligence.egg-info/dependency_links.txt`


## Python Compile Errors

- Errors: **0** (showing up to 50)


## Unreferenced Internal Modules (heuristic)

- Unreferenced: **188** (showing up to 100)

- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/agent/orchestrator.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/api/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/chatbot/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/chatbot/context_manager.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/chatbot/recommend_handler.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/core/logging.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/fusion/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/agent/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/legacy/agent/chat_responses.py`
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
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/monitoring/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/monitoring/alerts.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/monitoring/latency.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/rag/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/rag/ocr.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/rag_dsa/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/rag_dsa/build_index.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/services/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/services/alert_service.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/services/async_worker.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/classic_chat.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/config.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/handlers/cars.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/handlers/courses.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/handlers/electronics.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/handlers/electronics_catalog.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/handlers/news.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/streamlit_chatbot/handlers/places.py`
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
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/app/vision_local/index.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/__init__.py`
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
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/explainability/__init__.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/explainability/explainer_utils.py`
- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/src/uais/explainability/gradcam_explainer.py`

## Notes

- Duplicate files found with identical content hash (safe to consolidate later).
- Unreferenced internal modules found (may indicate duplicates/dead code).
- Data summary capped at 5000 files for: data/raw, data/processed

_Generated in 0.82s._
