# SENTIFARGO REPO AUDIT
- Generated: **2026-01-13T19:42:46**
- Repo: `/Users/pratik_n/Desktop/MyComputer/Sentifargo`

## 1) Tier estimate
**Score:** 93/100

**Tier guess:** Tier 5 (elite production-grade signals present)

**Signals:**
- +10: Repo scanned successfully
- +12: FastAPI app detected
- +8: 10+ API endpoints detected
- +8: Streamlit UI detected
- +8: Dockerfile present
- +6: docker-compose present
- +6: CI workflow present
- +4: docs/ present
- +5: Prometheus/metrics references found
- +6: Auth (JWT/OAuth) references found
- +6: MLflow/model registry references found
- +4: Explainability references found
- +4: YOLO/Ultralytics references found
- +3: FAISS references found
- +3: Transformer/RAG embeddings references found

## 2) Entry points
**Common entrypoints found:**
- `app/main.py`

**Files that look like FastAPI/uvicorn entry files:**
- `app/main.py`

## 3) Infrastructure / MLOps signals

### dockerfiles
- `Dockerfile`
- `Dockerfile.production`

### compose
- `docker-compose.production.yml`
- `docker-compose.yml`

### k8s
- (none found)

### github_actions
- `.github/workflows/ci-cd.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/deploy-pages.yml`

### makefiles
- `Makefile`

### requirements
- `requirements.txt`

### pyproject
- `pyproject.toml`

### precommit
- (none found)

### tests
- (none found)

### docs
- `data/docs/cybersecurity.md`
- `data/docs/fraud_detection.md`
- `data/docs/job_roles.md`
- `data/docs/Sentifargo_guide.md`
- `docs/ARCHITECTURE.md`
- `docs/LEGACY.md`
- `docs/MLOPS_ROADMAP.md`
- `docs/behavior_features.md`
- `docs/vision_labels.md`

### monitoring
- `app/models/recommender/metrics.py`
- `app/monitoring/metrics.py`
- `app/rag/metrics.py`
- `app/streamlit_chatbot/pages/metrics.py`
- `deploy/grafana/provisioning/datasources/datasource.yml`
- `deploy/prometheus/prometheus.yml`
- `experiments/behavior/metrics/metrics.csv`
- `experiments/behavior/metrics/metrics.json`
- `experiments/cyber/metrics/metrics.csv`
- `experiments/cyber/metrics/metrics.json`
- `experiments/fraud/ablations/none_metrics.csv`
- `experiments/fraud/metrics/metrics.csv`
- `experiments/fraud/metrics/metrics.json`
- `experiments/fusion/metrics/metrics.csv`
- `experiments/fusion/metrics/metrics.json`
- `experiments/recommender/metrics/metrics.json`
- `experiments/recommender/metrics/movielens_metrics.json`
- `experiments/recommender/metrics/recommender_metrics.json`
- `experiments/recommender/metrics/recommender_ncf_metrics.json`
- `experiments/vision/metrics/metrics.csv`
- `experiments/vision/video_temporal/metrics.json`
- `models/fraud/supervised_metrics.json`
- `models/vision/face_emotion/metrics.json`
- `notebooks/evaluation/70_voice_metrics.ipynb`
- `notebooks/evaluation/71_video_metrics.ipynb`
- `notebooks/evaluation/72_recommender_metrics.ipynb`
- `notebooks/evaluation/98_metrics_audit.ipynb`
- `notebooks/experiments/cyber/ablations/none_metrics.csv`
- `notebooks/experiments/fraud/ablations/binning_metrics.csv`
- `notebooks/experiments/fraud/ablations/mi_filter_metrics.csv`
- `notebooks/experiments/fraud/ablations/none_metrics.csv`
- `notebooks/experiments/fraud/ablations/poly_binning_metrics.csv`
- `notebooks/experiments/fraud/ablations/poly_metrics.csv`
- `notebooks/experiments/fraud/ablations/vif_binning_metrics.csv`
- `reports/metrics_behavior.csv`
- `reports/metrics_cyber.csv`
- `reports/metrics_fraud.csv`
- `reports/metrics_fusion.csv`
- `reports/metrics_vision.csv`
- `runs/mlflow/716084780746542089/5e8b1cce53ca42d6b583be0cb1b2823e/metrics/lr/pg0`
- `runs/mlflow/716084780746542089/5e8b1cce53ca42d6b583be0cb1b2823e/metrics/lr/pg1`
- `runs/mlflow/716084780746542089/5e8b1cce53ca42d6b583be0cb1b2823e/metrics/lr/pg2`
- `runs/mlflow/716084780746542089/5e8b1cce53ca42d6b583be0cb1b2823e/metrics/metrics/mAP50-95B`
- `runs/mlflow/716084780746542089/5e8b1cce53ca42d6b583be0cb1b2823e/metrics/metrics/mAP50B`
- `runs/mlflow/716084780746542089/5e8b1cce53ca42d6b583be0cb1b2823e/metrics/metrics/precisionB`
- `runs/mlflow/716084780746542089/5e8b1cce53ca42d6b583be0cb1b2823e/metrics/metrics/recallB`
- `runs/mlflow/716084780746542089/5e8b1cce53ca42d6b583be0cb1b2823e/metrics/train/box_loss`
- `runs/mlflow/716084780746542089/5e8b1cce53ca42d6b583be0cb1b2823e/metrics/train/cls_loss`
- `runs/mlflow/716084780746542089/5e8b1cce53ca42d6b583be0cb1b2823e/metrics/train/dfl_loss`
- `runs/mlflow/716084780746542089/5e8b1cce53ca42d6b583be0cb1b2823e/metrics/val/box_loss`
- `runs/mlflow/716084780746542089/5e8b1cce53ca42d6b583be0cb1b2823e/metrics/val/cls_loss`
- `runs/mlflow/716084780746542089/5e8b1cce53ca42d6b583be0cb1b2823e/metrics/val/dfl_loss`
- `runs/mlflow/716084780746542089/aa9002e01d824a44a3093b0ca960dc64/metrics/lr/pg0`
- `runs/mlflow/716084780746542089/aa9002e01d824a44a3093b0ca960dc64/metrics/lr/pg1`
- `runs/mlflow/716084780746542089/aa9002e01d824a44a3093b0ca960dc64/metrics/lr/pg2`
- `runs/mlflow/716084780746542089/aa9002e01d824a44a3093b0ca960dc64/metrics/train/box_loss`
- `runs/mlflow/716084780746542089/aa9002e01d824a44a3093b0ca960dc64/metrics/train/cls_loss`
- `runs/mlflow/716084780746542089/aa9002e01d824a44a3093b0ca960dc64/metrics/train/dfl_loss`
- `runs/mlflow/716084780746542089/cf765ddd49b34214be6801e68b6b76d6/metrics/lr/pg0`
- `runs/mlflow/716084780746542089/cf765ddd49b34214be6801e68b6b76d6/metrics/lr/pg1`

## 4) FastAPI overview
- FastAPI app files: **2**
  - `app/main.py`
  - `deploy/api/main.py`
- Endpoint decorators found: **51**

### include_router calls (sample)
- `app/main.py` includes `chat.router`
- `app/main.py` includes `rag.router`
- `app/main.py` includes `recommend.router`
- `app/main.py` includes `behavior.router`
- `app/main.py` includes `fraud.router`
- `app/main.py` includes `cyber.router`
- `app/main.py` includes `vision.router`
- `app/main.py` includes `_health_router`
- `app/main.py` includes `_app_risk_router`
- `app/main.py` includes `_app_monitor_router`
- `app/main.py` includes `_app_voice_router`
- `app/main.py` includes `_app_rag_router`
- `app/main.py` includes `_app_brand_router`
- `app/main.py` includes `_app_stt_router`
- `app/main.py` includes `_app_vision_temporal_router`

### Endpoints (sample)
- `GET` `/api/health`  (from `app/main.py` via `app`)
- `GET` `/`  (from `app/main.py` via `app`)
- `GET` `/`  (from `deploy/api/main.py` via `app`)
- `GET` `/health`  (from `deploy/api/main.py` via `app`)
- `POST` `/predict_fraud`  (from `deploy/api/main.py` via `app`)
- `POST` `/predict_cyber`  (from `deploy/api/main.py` via `app`)
- `POST` `/predict_fusion`  (from `deploy/api/main.py` via `app`)
- `POST` `/predict_nlp`  (from `deploy/api/main.py` via `app`)
- `POST` `/predict_vision`  (from `deploy/api/main.py` via `app`)
- `GET` `/health`  (from `app/core/health.py` via `router`)
- `GET` `/health/live`  (from `app/core/health.py` via `router`)
- `GET` `/health/ready`  (from `app/core/health.py` via `router`)
- `GET` `/health/detailed`  (from `app/core/health.py` via `router`)
- `GET` `/metrics`  (from `app/core/health.py` via `router`)
- `GET` `/ready`  (from `app/core/health.py` via `router`)
- `GET` `/events`  (from `app/api/cyber_timeline.py` via `router`)
- `GET` `/patterns`  (from `app/api/cyber_timeline.py` via `router`)
- `GET` `/sources`  (from `app/api/cyber_timeline.py` via `router`)
- `GET` `/summary`  (from `app/api/cyber_timeline.py` via `router`)
- `POST` `/log`  (from `app/api/monitor.py` via `router`)
- `GET` `/summary`  (from `app/api/monitor.py` via `router`)
- `GET` `/drift`  (from `app/api/monitor.py` via `router`)
- `GET` `/risk_summary`  (from `app/api/monitor.py` via `router`)
- `GET` `/events`  (from `app/api/monitor.py` via `router`)
- `POST` `/baseline/build`  (from `app/api/monitor.py` via `router`)
- `GET` `/health`  (from `app/api/health.py` via `router`)
- `POST` `/predict`  (from `app/api/vision_temporal.py` via `router`)
- `POST` `/speak`  (from `app/api/tts.py` via `router`)
- `POST` `/fraud`  (from `app/api/fraud.py` via `router`)
- `POST` `/emotion`  (from `app/api/voice.py` via `router`)
- `POST` `/chat`  (from `app/api/chat.py` via `router`)
- `POST` `/ingest`  (from `app/api/rag.py` via `router`)
- `POST` `/upload`  (from `app/api/rag.py` via `router`)
- `POST` `/analyze`  (from `app/api/fusion.py` via `router`)
- `POST` `/risk/analyze`  (from `app/api/risk.py` via `router`)
- `POST` `/predict`  (from `app/api/brand.py` via `router`)
- `POST` `/recommend`  (from `app/api/recommender.py` via `router`)
- `POST` `/recommend/explain`  (from `app/api/recommender.py` via `router`)
- `POST` `/recommend/multimodal`  (from `app/api/recommender.py` via `router`)
- `POST` `/transcribe`  (from `app/api/stt.py` via `router`)
- `POST` `/logs`  (from `app/legacy/api/routes/behavior.py` via `router`)
- `POST` `/train`  (from `app/legacy/api/routes/vision.py` via `router`)
- `POST` `/predict`  (from `app/legacy/api/routes/vision.py` via `router`)
- `POST` `/face_emotion/predict`  (from `app/legacy/api/routes/vision.py` via `router`)
- `POST` `/video/predict`  (from `app/legacy/api/routes/vision.py` via `router`)
- `POST` `/explain`  (from `app/legacy/api/routes/recommend.py` via `router`)
- `POST` `/multimodal`  (from `app/legacy/api/routes/recommend.py` via `router`)
- `POST` `/topn`  (from `app/legacy/api/routes/recommend.py` via `router`)
- `POST` `/multimodal`  (from `app/legacy/api/routes/chat.py` via `router`)
- `GET` `/stream`  (from `app/legacy/api/routes/chat.py` via `router`)
- `POST` `/query`  (from `app/legacy/api/routes/rag.py` via `router`)

## 5) Streamlit overview
- Streamlit files: **21**
- `app/agent/orchestrator.py`
- `app/legacy/agent/orchestrator.py`
- `app/legacy/api/routes/chat.py`
- `app/main.py`
- `app/streamlit_chatbot/app.py`
- `app/streamlit_chatbot/classic_chat.py`
- `app/streamlit_chatbot/pages/brand.py`
- `app/streamlit_chatbot/pages/chat.py`
- `app/streamlit_chatbot/pages/command_center.py`
- `app/streamlit_chatbot/pages/live.py`
- `app/streamlit_chatbot/pages/metrics.py`
- `app/streamlit_chatbot/pages/risk.py`
- `app/streamlit_chatbot/pages/tools.py`
- `app/streamlit_chatbot/pages/voice_chat.py`
- `app/streamlit_chatbot/recommender_router.py`
- `app/streamlit_chatbot/risk_dashboard.py`
- `app/streamlit_chatbot/ui/theme.py`
- `app/streamlit_chatbot/unified_chat.py`
- `dashboard/components/shap_viz.py`
- `scripts/check_production.py`
- `tests/test_clothes_catalog.py`

- Probable Streamlit page files:
- `app/streamlit_chatbot/classic_chat.py`
- `app/streamlit_chatbot/ui/theme.py`
- `app/streamlit_chatbot/unified_chat.py`
- `dashboard/components/shap_viz.py`

## 6) ML / Tech stack fingerprints

### catboost
- `requirements.txt`
- `configs/cyber_baseline.yaml`
- `configs/fraud_baseline.yaml`
- `configs/behavior_baseline.yaml`
- `src/uais/supervised/train_fraud_supervised.py`
- `src/uais/supervised/train_cyber_supervised.py`
- `dashboard/components/shap_viz.py`

### faiss
- `PROJECT_SUMMARY.md`
- `requirements.txt`
- `README.md`
- `app/main.py`
- `tests/test_health_endpoint.py`
- `docs/ARCHITECTURE.md`
- `scripts/build_recommender_index.py`
- `app/rag/vector_store.py`
- `app/vision_local/index.py`
- `app/models/recommender/index.py`
- `app/models/recommender/multimodal/build_index.py`
- `app/models/recommender/multimodal/__init__.py`
- `app/models/recommender/multimodal/multimodal_predict.py`
- `app/models/recommender/multimodal/index_store.py`
- `app/legacy/api/routes/recommend.py`
- `app/streamlit_chatbot/ui/theme.py`

### grafana
- `PROJECT_AUDIT_REPORT.md`
- `README.md`
- `docker-compose.production.yml`
- `docs/ARCHITECTURE.md`
- `scripts/check_production.py`

### jwt
- `PROJECT_AUDIT_REPORT.md`
- `docs/ARCHITECTURE.md`

### keras
- `src/uais/vision/train_vision_model.py`
- `src/uais/generative/train_vae.py`
- `src/uais_v/training/train_30seq.py`
- `src/uais_v/models/seq_encoder_tf.py`
- `src/uais_v/models/multi_sequence_30_tf.py`
- `runs/mlflow/716084780746542089/5e8b1cce53ca42d6b583be0cb1b2823e/artifacts/args.yaml`
- `runs/detect/brand_final/args.yaml`
- `runs/detect/train11/args.yaml`
- `runs/detect/train10/args.yaml`
- `runs/detect/train2/args.yaml`
- `runs/detect/train5/args.yaml`
- `runs/detect/train4/args.yaml`
- `runs/detect/train3/args.yaml`
- `runs/detect/brand_production/args.yaml`
- `runs/detect/brand_quick/args.yaml`
- `runs/detect/train/args.yaml`
- `runs/detect/brand_logodet3k/args.yaml`
- `runs/detect/train12/args.yaml`
- `runs/detect/train13/args.yaml`
- `runs/detect/train8/args.yaml`
- `runs/detect/train6/args.yaml`
- `runs/detect/brand_full/args.yaml`
- `runs/detect/brand_prod/args.yaml`
- `runs/detect/train7/args.yaml`
- `runs/detect/brand_logodet3k_v2/args.yaml`
- `runs/detect/train9/args.yaml`
- `models/brand/full/args.yaml`
- `models/brand/yolo_logodet/args.yaml`
- `models/brand/full_training/args.yaml`
- `models/brand/fast_run_1epoch/args.yaml`

### lightgbm
- `requirements.txt`
- `GAP_ANALYSIS.md`
- `README.md`
- `docs/ARCHITECTURE.md`
- `configs/cyber_baseline.yaml`
- `configs/fraud_baseline.yaml`
- `configs/base_config.yaml`
- `configs/behavior_baseline.yaml`
- `reports/model_comparison.md`
- `src/uais/supervised/train_fraud_supervised.py`
- `src/uais/supervised/train_cyber_supervised.py`
- `dashboard/components/shap_viz.py`

### lime
- `requirements.txt`
- `src/universal_anomaly_intelligence.egg-info/SOURCES.txt`
- `src/uais/explainability/runner.py`
- `src/uais/explainability/lime_explainer.py`
- `src/uais/explainability/__init__.py`

### mlflow
- `PROJECT_AUDIT_REPORT.md`
- `requirements.txt`
- `GAP_ANALYSIS.md`
- `requirements-optional.txt`
- `README.md`
- `mlflow_config.yaml`
- `docs/ARCHITECTURE.md`
- `docs/MLOPS_ROADMAP.md`
- `configs/cyber_baseline.yaml`
- `configs/fraud_baseline.yaml`
- `configs/behavior_baseline.yaml`
- `src/pipeline/train_models.py`
- `src/universal_anomaly_intelligence.egg-info/SOURCES.txt`
- `src/uais/utils/mlflow_utils.py`
- `runs/mlflow/690575434915126183/meta.yaml`
- `runs/mlflow/716084780746542089/meta.yaml`
- `runs/mlflow/0/meta.yaml`
- `runs/mlflow/258724143996341502/meta.yaml`
- `runs/mlflow/737381424675970088/meta.yaml`
- `runs/mlflow/737381424675970088/21bb448d52ef4dcb9d69a43e12213663/meta.yaml`
- `runs/mlflow/737381424675970088/686d00fdf22e42adb9ab56fbcab350b0/meta.yaml`
- `runs/mlflow/737381424675970088/dde6c05d05754c9a8755c77b37f909f4/meta.yaml`
- `runs/mlflow/737381424675970088/c6ec16fd1552409fa5ffeb72375b2603/meta.yaml`
- `runs/mlflow/737381424675970088/423917e4418a4d329c8f8ba3b3d4cbe7/meta.yaml`
- `runs/mlflow/737381424675970088/417117cbefca432dbc52a51be0d1bd3b/meta.yaml`
- `runs/mlflow/737381424675970088/d0954de194014d82a6e5dfa63fd3ae75/meta.yaml`
- `runs/mlflow/737381424675970088/8e5127bb0e624222b642a728481a696f/meta.yaml`
- `runs/mlflow/737381424675970088/fb5726140a6c4eda8948bf7ced179251/meta.yaml`
- `runs/mlflow/737381424675970088/5663d1ea4b0e48e1874444b5948d428a/meta.yaml`
- `runs/mlflow/737381424675970088/7de6b75aa04248f19bb90c3271f9c377/meta.yaml`

### prometheus
- `PROJECT_AUDIT_REPORT.md`
- `requirements.txt`
- `README.md`
- `docker-compose.production.yml`
- `requirements-ci.txt`
- `app/main.py`
- `tests/test_production.py`
- `docs/ARCHITECTURE.md`
- `scripts/check_production.py`
- `deploy/prometheus/prometheus.yml`
- `deploy/grafana/provisioning/datasources/datasource.yml`
- `app/core/config.py`
- `app/core/health.py`

### sentence_transformers
- `app/rag/embed.py`

### shap
- `PROJECT_SUMMARY.md`
- `requirements.txt`
- `GAP_ANALYSIS.md`
- `tests/test_fusion_run.py`
- `tests/test_nlp_tiny.py`
- `tests/test_voice_noise.py`
- `tests/test_multi_sequence_30_torch.py`
- `tests/test_multi_sequence_30_tf.py`
- `tests/test_build_30seq_dataset.py`
- `tests/test_api_payloads.py`
- `tests/test_vision_resnet.py`
- `docs/ARCHITECTURE.md`
- `docs/LEGACY.md`
- `scripts/train_production.py`
- `scripts/retrain_all_98.py`
- `scripts/ci_smoke.py`
- `src/pipeline/build_features.py`
- `src/universal_anomaly_intelligence.egg-info/SOURCES.txt`
- `src/scripts/run_fraud_experiment.py`
- `src/uais/fusion/run_fusion.py`
- `src/uais/fusion/build_embeddings.py`
- `src/uais/fusion/train_fusion_model.py`
- `src/uais/anomaly/train_isolation_forest.py`
- `src/uais/ensembles/blending.py`
- `src/uais/ensembles/stacking.py`
- `src/uais/experiments/feature_ablation.py`
- `src/uais/features/cyber_features.py`
- `src/uais/features/behavior_features.py`
- `src/uais/vision/train_vision_model.py`
- `src/uais/explainability/runner.py`

### sklearn
- `benchmarks/benchmark_suite.py`
- `scripts/train_production.py`
- `scripts/generate_benchmarks.py`
- `scripts/retrain_all_98.py`
- `scripts/train_all_vision_full.py`
- `scripts/train_all.py`
- `reports/codex_audit_20251213_120625.md`
- `src/pipeline/train_models.py`
- `src/scripts/run_cyber_experiment.py`
- `src/scripts/run_fraud_experiment.py`
- `src/scripts/run_behavior_experiment.py`
- `src/scripts/run_fusion_experiment.py`
- `src/train/train_video_temporal.py`
- `src/train/train_movielens_recommender.py`
- `src/train/train_recommender.py`
- `src/train/train_fusion.py`
- `src/uais/fusion/run_fusion.py`
- `src/uais/fusion/build_embeddings.py`
- `src/uais/fusion/train_fusion_model.py`
- `src/uais/anomaly/train_isolation_forest.py`
- `src/uais/anomaly/train_ocsvm.py`
- `src/uais/anomaly/train_lof.py`
- `src/uais/anomaly/train_autoencoder.py`
- `src/uais/ensembles/stacking.py`
- `src/uais/experiments/feature_ablation.py`
- `src/uais/features/cyber_features.py`
- `src/uais/features/scalers_encoders.py`
- `src/uais/features/behavior_features.py`
- `src/uais/utils/metrics.py`
- `src/uais/utils/plotting.py`

### tensorflow
- `requirements.txt`
- `tests/test_multi_sequence_30_tf.py`
- `reports/codex_audit_20251213_120625.md`
- `src/uais/vision/train_vision_model.py`
- `src/uais/generative/train_vae.py`
- `src/uais_v/training/train_30seq.py`
- `src/uais_v/utils/seed.py`
- `src/uais_v/models/seq_encoder_tf.py`
- `src/uais_v/models/multi_sequence_30_tf.py`
- `src/uais_v/cli/main.py`
- `data/docs/job_roles.md`
- `app/legacy/api/routes/vision.py`

### torch
- `PROJECT_SUMMARY.md`
- `PROJECT_AUDIT_REPORT.md`
- `requirements.txt`
- `requirements-optional.txt`
- `README.md`
- `EXECUTIVE_SUMMARY.md`
- `PROJECT_DOCUMENTATION.md`
- `app/main.py`
- `tests/test_nlp_tiny.py`
- `tests/test_multi_sequence_30_torch.py`
- `tests/test_vision_resnet.py`
- `benchmarks/benchmark_suite.py`
- `configs/model_30seq.yaml`
- `scripts/prepare_intel_scene_vision.py`
- `scripts/import_celeb_v2_vision.py`
- `scripts/train_all_vision_full.py`
- `reports/model_comparison.md`
- `src/universal_anomaly_intelligence.egg-info/SOURCES.txt`
- `src/train/train_brand_logo_detector.py`
- `src/train/train_face_emotion.py`
- `src/train/train_video_temporal.py`
- `src/uais/explainability/vision_gradcam.py`
- `src/uais/sequence/transformer_tcn.py`
- `src/uais/sequence/train_gru.py`
- `src/uais/sequence/train_lstm.py`
- `src/uais_v/training/train_30seq_torch.py`
- `src/uais_v/training/train_nlp.py`
- `src/uais_v/training/train_vision.py`
- `src/uais_v/training/train_30seq.py`
- `src/uais_v/utils/seed.py`

### transformers
- `PROJECT_SUMMARY.md`
- `conftest.py`
- `pytest.ini`
- `requirements.txt`
- `app/main.py`
- `tests/test_nlp_tiny.py`
- `src/uais/experiments/feature_ablation.py`
- `src/uais/features/scalers_encoders.py`
- `src/uais/preprocessing/pipeline.py`
- `src/uais_v/training/train_nlp.py`
- `src/uais_v/models/nlp_text_model.py`
- `app/core/logging.py`
- `app/rag/embed.py`
- `app/vision_local/embedder.py`
- `app/models/recommender/multimodal/image_embed.py`
- `app/legacy/agent/chat_responses.py`

### ultralytics
- `requirements.txt`
- `scripts/train_production.py`
- `scripts/train_all.py`
- `src/train/train_brand_logo_detector.py`
- `src/vision/brand/recognizer.py`
- `src/vision/brand/data_utils.py`
- `runs/mlflow/716084780746542089/meta.yaml`
- `app/api/brand.py`

### xgboost
- `PROJECT_SUMMARY.md`
- `requirements.txt`
- `GAP_ANALYSIS.md`
- `README.md`
- `EXECUTIVE_SUMMARY.md`
- `PROJECT_DOCUMENTATION.md`
- `app/main.py`
- `docs/ARCHITECTURE.md`
- `configs/cyber_baseline.yaml`
- `configs/fraud_baseline.yaml`
- `configs/behavior_baseline.yaml`
- `scripts/generate_benchmarks.py`
- `reports/model_comparison.md`
- `src/uais/supervised/train_fraud_supervised.py`
- `src/uais/supervised/train_cyber_supervised.py`
- `data/docs/fraud_detection.md`
- `dashboard/components/shap_viz.py`
- `app/legacy/agent/chat_responses.py`
- `app/legacy/api/routes/fraud.py`
- `app/legacy/api/routes/recommend.py`

### yolo
- `PROJECT_AUDIT_REPORT.md`
- `GAP_ANALYSIS.md`
- `README.md`
- `PROJECT_DOCUMENTATION.md`
- `artifacts/README.md`
- `tests/test_brand_routes_import.py`
- `docs/ARCHITECTURE.md`
- `docs/vision_labels.md`
- `scripts/train_production.py`
- `scripts/prepare_brand_data.py`
- `scripts/README.md`
- `scripts/train_all.py`
- `scripts/train_all_vision.py`
- `data/README.md`
- `notebooks/README.md`
- `reports/model_comparison.md`
- `src/train/train_brand_logo_detector.py`
- `src/vision/brand/recognizer.py`
- `src/vision/brand/data_utils.py`
- `runs/mlflow/737381424675970088/417117cbefca432dbc52a51be0d1bd3b/meta.yaml`
- `runs/mlflow/716084780746542089/5e8b1cce53ca42d6b583be0cb1b2823e/artifacts/args.yaml`
- `runs/detect/brand_final/args.yaml`
- `runs/detect/train11/args.yaml`
- `runs/detect/train10/args.yaml`
- `runs/detect/train2/args.yaml`
- `runs/detect/train5/args.yaml`
- `runs/detect/train4/args.yaml`
- `runs/detect/train3/args.yaml`
- `runs/detect/brand_production/args.yaml`
- `runs/detect/brand_quick/args.yaml`

## 7) Datasets folder snapshot
- `data/` found. (showing up to ~200 dirs)
- `data/Celeb_V2` (files: 0)
- `data/Celeb_V2/Test` (files: 0)
- `data/Celeb_V2/Test/fake` (files: 5067)
- `data/Celeb_V2/Test/real` (files: 5036)
- `data/Celeb_V2/Train` (files: 0)
- `data/Celeb_V2/Train/fake` (files: 40536)
- `data/Celeb_V2/Train/real` (files: 40288)
- `data/Celeb_V2/Val` (files: 0)
- `data/Celeb_V2/Val/fake` (files: 5068)
- `data/Celeb_V2/Val/real` (files: 5036)
- `data/Video-2` (files: 1)
- `data/Video-2/Celeb-real` (files: 590)
- `data/Video-2/Celeb-synthesis` (files: 5639)
- `data/Video-2/YouTube-real` (files: 300)
- `data/catalogs` (files: 1)
- `data/docs` (files: 7)
- `data/embeddings` (files: 6)
- `data/interim` (files: 1)
- `data/monitoring` (files: 0)
- `data/monitoring/baseline` (files: 1)
- `data/monitoring/live` (files: 1)
- `data/monitoring/logs` (files: 2)
- `data/processed` (files: 0)
- `data/processed/behavior` (files: 1)
- `data/processed/brand_yolo` (files: 2)
- `data/processed/brand_yolo/images` (files: 0)
- `data/processed/brand_yolo/labels` (files: 2)
- `data/processed/cyber` (files: 1)
- `data/processed/fraud` (files: 1)
- `data/processed/recommender` (files: 0)
- `data/processed/vision` (files: 0)
- `data/processed/vision/train` (files: 0)
- `data/processed/vision/val` (files: 0)
- `data/processed/voice` (files: 0)
- `data/raw` (files: 0)
- `data/raw/archive` (files: 6)
- `data/raw/behavior` (files: 2)
- `data/raw/behavior/_archive_r4_2` (files: 0)
- `data/raw/behavior/r4.2` (files: 8)
- `data/raw/brand` (files: 1)
- `data/raw/brand/LogoDet-3K` (files: 4)
- `data/raw/crema_d` (files: 0)
- `data/raw/crema_d/audio_wav` (files: 7442)
- `data/raw/crema_d/labels` (files: 1)
- `data/raw/crema_d/video` (files: 7442)
- `data/raw/cyber` (files: 8)
- `data/raw/cyber/_archive_unsw_nb15` (files: 8)
- `data/raw/fraud` (files: 1)
- `data/raw/fraud/paysim` (files: 1)
- `data/raw/nlp` (files: 0)
- `data/raw/nlp/fakenews` (files: 1)
- `data/raw/recommendation` (files: 11)
- `data/raw/recommendation/_archive_electronics` (files: 2)
- `data/raw/recommendation/yelp` (files: 6)
- `data/raw/recommender` (files: 0)
- `data/raw/vision` (files: 1)
- `data/raw/vision/_archive_intel` (files: 0)
- `data/raw/vision/datasets` (files: 0)
- `data/raw/vision/face_emotion` (files: 3)
- `data/raw/vision/train_fake` (files: 0)
- `data/raw/vision/train_real` (files: 0)
- `data/raw/vision/video` (files: 0)
- `data/raw/voice` (files: 0)
- `data/raw/voice/_ravdess` (files: 0)
- `data/raw/voice/_tess` (files: 0)
- `data/raw/voice/angry` (files: 1863)
- `data/raw/voice/happy` (files: 1863)
- `data/raw/voice/neutral` (files: 1775)
- `data/raw/voice/sad` (files: 1863)
- `data/synthetic` (files: 2)

## 8) Repo stats
- Total files scanned: **1045541**

### Top 20 largest files
- `data/raw/behavior/r4.2/http.csv` — 14,536,257,467 bytes
- `data/raw/recommendation/yelp/yelp_academic_dataset_review.json` — 5,341,868,833 bytes
- `data/raw/behavior/r4.2.tar.bz2` — 4,824,287,500 bytes
- `data/raw/recommendation/yelp/yelp_academic_dataset_user.json` — 3,363,329,011 bytes
- `data/raw/recommendation/Electronics_5.json` — 1,478,965,298 bytes
- `data/raw/behavior/r4.2/email.csv` — 1,362,101,939 bytes
- `data/raw/recommendation/movielens.csv` — 690,353,377 bytes
- `data/raw/archive/rating.csv` — 690,353,377 bytes
- `data/raw/recommendation/electronics_small.csv` — 681,420,010 bytes
- `data/raw/recommendation/_archive_electronics/electronics_small.csv` — 681,420,010 bytes
- `data/raw/fraud/paysim/paysim_transactions.csv` — 493,534,783 bytes
- `data/processed/cyber/unsw_nb15_features.parquet` — 450,605,781 bytes
- `data/raw/recommendation/ratings_Electronics.csv` — 318,766,497 bytes
- `data/raw/recommendation/yelp/yelp_academic_dataset_checkin.json` — 286,958,945 bytes
- `data/embeddings/recommender_vectors.npy` — 279,531,648 bytes
- `models/behavior.pkl` — 230,334,637 bytes
- `models/behavior/behavior_best.pkl` — 230,334,607 bytes
- `data/raw/archive/genome_scores.csv` — 214,322,450 bytes
- `data/raw/behavior/r4.2/file.csv` — 193,055,265 bytes
- `data/raw/recommendation/yelp/yelp_academic_dataset_tip.json` — 180,604,475 bytes

## 9) Quick command outputs

### python --version
```text
Python 3.13.5

```

### pip freeze (truncated)
```text
absl-py==2.3.1
aext-assistant @ file:///private/var/folders/nz/j6p8yfhx1mv_0grj5xl4650h0000gp/T/abs_d5fxz3l2ix/croot/aext-assistant_1746560160060/work
aext-assistant-server @ file:///private/var/folders/nz/j6p8yfhx1mv_0grj5xl4650h0000gp/T/abs_1emcn1_yt0/croot/aext-assistant-server_1746552985810/work
aext-core @ file:///private/var/folders/k1/30mswbxs7r1g6zwn8y4fyt500000gp/T/abs_2eg8ig5bzd/croot/aext-core_1746546095117/work
aext-core-server @ file:///private/var/folders/k1/30mswbxs7r1g6zwn8y4fyt500000gp/T/abs_1eo4dumd8o/croot/aext-core-server_1746542359934/work
aext-panels @ file:///private/var/folders/k1/30mswbxs7r1g6zwn8y4fyt500000gp/T/abs_88neb0jwio/croot/aext-panels_1746560092300/work
aext-panels-server @ file:///private/var/folders/k1/30mswbxs7r1g6zwn8y4fyt500000gp/T/abs_f8jcm1930j/croot/aext-panels-server_1746552964188/work
aext-project-filebrowser-server @ file:///private/var/folders/k1/30mswbxs7r1g6zwn8y4fyt500000gp/T/abs_32_va59s0l/croot/aext-project-filebrowser-server_1746562207762/work/backend_lib/project_filebrowser
aext-share-notebook @ file:///private/var/folders/nz/j6p8yfhx1mv_0grj5xl4650h0000gp/T/abs_355mar42bl/croot/aext-share-notebook_1746556798423/work
aext-share-notebook-server @ file:///private/var/folders/nz/j6p8yfhx1mv_0grj5xl4650h0000gp/T/abs_c8l1ebgxcq/croot/aext-share-notebook-server_1746552715655/work
aext-shared @ file:///private/var/folders/k1/30mswbxs7r1g6zwn8y4fyt500000gp/T/abs_9etxpmoe8u/croot/aext-shared_1746540522024/work
aext-toolbox @ file:///private/var/folders/k1/30mswbxs7r1g6zwn8y4fyt500000gp/T/abs_4fo05xs80k/croot/anaconda-toolbox_1747230963854/work
aext_environments_server @ file:///private/var/folders/k1/30mswbxs7r1g6zwn8y4fyt500000gp/T/abs_44sltsc9tr/croot/aext-environments-server_1746560394654/work/backend_lib/environments
aiobotocore @ file:///private/var/folders/nz/j6p8yfhx1mv_0grj5xl4650h0000gp/T/abs_b2htsn1rgl/croot/aiobotocore_1738237874912/work
aiohappyeyeballs @ file:///private/var/folders/nz/j6p8yfhx1mv_0grj5xl4650h0000gp/T/abs_b38qlemj37/croot/aiohappyeyeballs_1734469403568/work
aiohttp @ file:///private/var/folders/nz/j6p8yfhx1mv_0grj5xl4650h0000gp/T/abs_44bhte2f2d/croot/aiohttp_1734692700992/work
aioitertools @ file:///tmp/build/80754af9/aioitertools_1607109665762/work
aiosignal @ file:///tmp/build/80754af9/aiosignal_1637843061372/work
aiosqlite==0.21.0
alabaster @ file:///Users/builder/cbouss/perseverance-python-buildout/croot/alabaster_1728591579756/work
alembic @ file:///opt/miniconda3/conda-bld/alembic_1760520175076/work
altair @ file:///private/var/folders/k1/30mswbxs7r1g6zwn8y4fyt500000gp/T/abs_7ew3pavrjt/croot/altair_1743016738697/work
anaconda-anon-usage @ file:///private/var/folders/k1/30mswbxs7r1g6zwn8y4fyt500000gp/T/abs_degjgm8ut1/croot/anaconda-anon-usage_1749054786234/work
anaconda-auth @ file:///private/var/folders/k1/30mswbxs7r1g6zwn8y4fyt500000gp/T/abs_c9m1keso7m/croot/anaconda-cloud-auth-split_1747863789573/work
anaconda-catalogs @ file:///private/var/folders/k1/30mswbxs7r1g6zwn8y4fyt500000gp/T/abs_90e2gpmhv3/croot/anaconda-catalogs_1747774728177/work
anaconda-cli-base @ file:///private/var/folders/nz/j6p8yfhx1mv_0grj5xl4650h0000gp/T/abs_08m4xcbj7q/croot/anaconda-cli-base_1741369478940/work
anaconda-client @ file:///private/var/folders/k1/30mswbxs7r1g6zwn8y4fyt500000gp/T/abs_52pw426gad/croot/anaconda-client_1743199588333/work
anaconda-navigator @ file:///private/var/folders/nz/j6p8yfhx1mv_0grj5xl4650h0000gp/T/abs_57gf3vgn69/croot/anaconda-navigator_1749737717526/work
anaconda-project @ file:///private/var/folders/k1/30mswbxs7r1g6zwn8y4fyt500000gp/T/abs_dcsecg0xhr/croot/anaconda-project_1746215306884/work
annotated-doc==0.0.3
annotated-types @ file:///Users/builder/cbouss/perseverance-python-buildout/croot/annotated-types_1728588668736/work
anyio @ file:///private/var/folders/k1/30mswbxs7r1g6zwn8y4fyt500000gp/T/abs_d9l4uro_qv/croot/anyio_1745334654441/work
appdirs==1.4.4
applaunchservices @ file:///Users/builder/cbouss/perseverance-python-buildout/croot/applaunchservices_1728595929050/work
appnope @ file:///Users/builder/cbouss/perseverance-python-buildout/croot/appnope_1728587432692/work
apprise==1.9.5
appscript @ file:///private/var/folders/k1/30mswbxs7r1g6zwn8y4fyt500000gp/T/abs_1abn3g1r3s/croot/appscript_1738045930024/work
archspec @ file:///croot/archspec_1709217642129/work
argon2-cffi @ file:///opt/conda/conda-bld/argon2-cffi_1645000214183/work
argon2-cffi-bindings @ file:///private/var/folders/nz/j6p8yfhx1mv_0grj5xl4650h0000gp/T/abs_2ef471wnyf/croot/argon2-cffi-bindings_1736182451265/work
arrow @ file:///Users/builder/cbouss/perseverance-python-buildout/croot/arrow_1731714085106/work
asgi-lifespan==2.1.0
astroid @ file:///Users/builder/cbouss/buildout/croot/astroid_1739484442213/work
astropy @ file:///private/var/folders/k1/30mswbxs7r1g6zwn8y4fyt500000gp/T/abs_a0fm0x2tco/croot/astropy_1738094414286/work
astropy-iers-data @ file:///private/var/folders/nz/j6p8yfhx1mv_0grj5xl4650h0000gp/T/abs_94mvdt0ezd/croot/astropy-iers-data_1737137597239/work
asttokens @ file:///private/var/folders/nz/j6p8yfhx1mv_0grj5xl4650h0000gp/T/abs_11i8cnwuxs/croot/asttokens_1743630449718/work
astunparse==1.6.3
async-lru @ file:///Users/builder/cbouss/perseverance-python-buildout/croot/async-lru_1728588685926/work
asyncpg==0.31.0
asyncssh @ file:///Users/builder/cbouss/buildout/croot/asyncssh_1732921222384/work
atomicwrites==1.4.0
attrs @ file:///private/var/folders/nz/j6p8yfhx1mv_0grj5xl4650h0000gp/T/abs_93pjmt0git/croot/attrs_1734533120523/work
audioop-lts==0.2.2
audioread==3.1.0
autogluon.common==1.4.1b20251201
autogluon.core==1.4.1b20251201
autogluon.features==1.4.1b20251201
autogluon.tabular==1.4.1b20251201
Automat @ file:///private/var/folders/k1/30mswbxs7r1g6zwn8y4fyt500000gp/T/abs_ddy0059olt/croot/automat_1743532570194/work
autopep8 @ file:///croot/autopep8_1708962882016/work
babel @ file:///private/var/folders/k1/30mswbxs7r1g6zwn8y4fyt500000gp/T/abs_ed2j11k3aq/croot/babel_1737454371799/work
bcrypt @ file:///private/var/folders/nz/
```

### pytest -q (may fail if env not set)
```text
============================= test session starts ==============================
platform darwin -- Python 3.13.5, pytest-8.3.4, pluggy-1.6.0
rootdir: /Users/pratik_n/Desktop/MyComputer/Sentifargo
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.7.0

----------------------------- live log collection ------------------------------
2026-01-13 19:42:37 [INFO] NumExpr defaulting to 10 threads.
2026-01-13 19:42:40 [INFO] Production middleware configured successfully
collected 78 items / 1 skipped

tests/test_api_payloads.py::test_fusion_keys_sorted_for_payload PASSED   [  1%]
tests/test_behavior_logs_api.py::test_behavior_logs_endpoint_accepts_csv 
-------------------------------- live log call ---------------------------------
2026-01-13 19:42:40 [INFO] Request started: POST /api/behavior/logs request_id=38ff1210-9f2a-4134-b011-b63a656a9496 client=testclient
2026-01-13 19:42:40 [INFO] Request completed: POST /api/behavior/logs status=200 duration=17.10ms request_id=38ff1210-9f2a-4134-b011-b63a656a9496
2026-01-13 19:42:40 [INFO] HTTP Request: POST http://testserver/api/behavior/logs?max_rows=1000&top_n=5 "HTTP/1.1 200 OK"
PASSED                                                                   [  2%]
tests/test_brand_routes_import.py::test_brand_route_import_does_not_require_weights PASSED [  3%]
tests/test_build_30seq_dataset.py::test_build_sequences_writes_files PASSED [  5%]
tests/test_build_recommender_index_script.py::test_build_recommender_index_script_runs PASSED [  6%]
tests/test_chat.py::test_chat_route 
-------------------------------- live log call ---------------------------------
2026-01-13 19:42:41 [INFO] Request started: POST /api/chat request_id=9d8ca8f1-b26b-4b26-97c3-0f6c539fcbe3 client=testclient
2026-01-13 19:42:41 [INFO] Request completed: POST /api/chat status=200 duration=114.80ms request_id=9d8ca8f1-b26b-4b26-97c3-0f6c539fcbe3
2026-01-13 19:42:41 [INFO] HTTP Request: POST http://testserver/api/chat "HTTP/1.1 200 OK"
PASSED                                                                   [  7%]
tests/test_chat_multimodal_stt.py::test_chat_multimodal_transcribe_flag_does_not_break 
-------------------------------- live log call ---------------------------------
2026-01-13 19:42:41 [INFO] Request started: POST /api/chat/multimodal request_id=b82ba926-0246-4bb3-9ff0-284bc9ad4468 client=testclient
2026-01-13 19:42:42 [INFO] Request completed: POST /api/chat/multimodal status=200 duration=980.06ms request_id=b82ba926-0246-4bb3-9ff0-284bc9ad4468
2026-01-13 19:42:42 [INFO] HTTP Request: POST http://testserver/api/chat/multimodal "HTTP/1.1 200 OK"
PASSED                                                                   [  8%]
tests/test_clothes_catalog.py::test_recommend_clothes_includes_brand_and_title PASSED [ 10%]
tests/test_clothes_catalog.py::test_recommend_clothes_works_without_preferred_tags PASSED [ 11%]
tests/test_decision_engine.py::test_make_decision_blocks_on_high_fraud PASSED [ 12%]
tests/test_decision_engine.py::test_make_decision_step_up_on_combined_risk PASSED [ 14%]
tests/test_decision_engine.py::test_make_decision_allows_low_risk PASSED [ 15%]
tests/test_face_emotion_endpoint.py::test_face_emotion_predict_no_file 
-------------------------------- live log call ---------------------------------
2026-01-13 19:42:42 [INFO] Request started: POST /api/vision/face_emotion/predict request_id=a37d40c7-b268-409e-9f4b-9ee1a5f663c1 client=testclient
2026-01-13 19:42:42 [INFO] Request completed: POST /api/vision/face_emotion/predict status=422 duration=0.75ms request_id=a37d40c7-b268-409e-9f4b-9ee1a5f663c1
2026-01-13 19:42:42 [INFO] HTTP Request: POST http://testserver/api/vision/face_emotion/predict "HTTP/1.1 422 Unprocessable Entity"
PASSED                                                                   [ 16%]
tests/test_face_emotion_endpoint.py::test_face_emotion_predict_invalid_file 
-------------------------------- live log call ---------------------------------
2026-01-13 19:42:42 [INFO] Request started: POST /api/vision/face_emotion/predict request_id=07531b09-eddf-4e7a-85f3-cec83ea84c68 client=testclient
2026-01-13 19:42:42 [INFO] Request completed: POST /api/vision/face_emotion/predict status=400 duration=0.87ms request_id=07531b09-eddf-4e7a-85f3-cec83ea84c68
2026-01-13 19:42:42 [INFO] HTTP Request: POST http://testserver/api/vision/face_emotion/predict "HTTP/1.1 400 Bad Request"
PASSED                                                                   [ 17%]
tests/test_fusion_run.py::test_generate_meta_features_and_train PASSED   [ 19%]
tests/test_health.py::test_health_endpoint 
-------------------------------- live log call ---------------------------------
2026-01-13 19:42:42 [INFO] Request started: GET /health request_id=2ba20d27-f8d1-446c-b3cb-ca74ed0c409b client=testclient
2026-01-13 19:42:42 [INFO] Request completed: GET /health status=200 duration=0.63ms request_id=2ba20d27-f8d1-446c-b3cb-ca74ed0c409b
2026-01-13 19:42:42 [INFO] HTTP Request: GET http://testserver/health "HTTP/1.1 200 OK"
PASSED                                                                   [ 20%]
tests/test_health_endpoint.py::test_api_health_contract 
-------------------------------- live log call ---------------------------------
2026-01-13 19:42:42 [INFO] Request started: GET /api/health request_id=4f50ffcf-cb81-49da-8126-822c959f82ef client=testclient
2026-01-13 19:42:42 [INFO] Request completed: GET /api/health status=200 duration=0.87ms request_id=4f50ffcf-cb81-49da-8126-822c959f82ef
2026-01-13 19:42:42 [INFO] HTTP Request: GET http://testserver/api/health "HTTP/1.1 200 OK"
FAILED                                                                   [ 21%]
tests/test_monitoring.py::test_monitor_workflow 
-------------------------------- live log call ---------------------------------
2026-01-13 19:42:42 [INFO] Request started: POST /api/monitor/log request_id=cbd6835d-4340-4863-85a3-cd0ac537b1f0 client=testclient
2026-01-13 19:42:42 [INFO] Request completed: POST /api/monitor/log status=200 duration=0.94ms request_id=cbd6835d-4340-4863-85a3-cd0ac537b1f0
2026-01-13 19:42:42 [INFO] HTTP Request: POST http://testserver/api/monitor/log "HTTP/1.1 200 OK"
2026-01-13 19:42:42 [INFO] Request started: GET /api/monitor/summary request_id=d18cab63-cb4a-4be7-8ddd-a4cbea5deba3 client=testclient
2026-01-13 19:42:42 [INFO] Request completed: GET /api/monitor/summary status=200 duration=1.03ms request_id=d18cab63-cb4a-4be7-8ddd-a4cbea5deba3
2026-01-13 19:42:42 [INFO] HTTP Request: GET http://testserver/api/monitor/summary?window_n=10 "HTTP/1.1 200 OK"
2026-01-13 19:42:42 [INFO] Request started: POST /api/monitor/baseline/build request_id=de1d01c6-6b68-484a-bd32-73117faa5f2d client=testclient
2026-01-13 19:42:42 [INFO] Request completed: POST /api/monitor/baseline/build status=200 duration=0.70ms request_id=de1d01c6-6b68-484a-bd32-73117faa5f2d
2026-01-13 19:42:42 [INFO] HTTP Request: POST http://testserver/api/monitor/baseline/build "HTTP/1.1 200 OK"
2026-01-13 19:42:42 [INFO] Request started: GET /api/monitor/drift request_id=c57f8649-9443-4320-b8b4-7e43ef82b79b client=testclient
2026-01-13 19:42:42 [INFO] Request completed: GET /api/monitor/drift status=200 duration=0.48ms request_id=c57f8649-9443-4320-b8b4-7e43ef82b79b
2026-01-13 19:42:42 [INFO] HTTP Request: GET http://testserver/api/monitor/drift?window_n=10 "HTTP/1.1 200 OK"
PASSED                                                                   [ 23%]
tests/test_multi_sequence_30_torch.py::test_forward_pass_small_shape PASSED [ 24%]
tests/test_nlp_tiny.py::test_distilbert_forward_smoke SKIPPED (could...) [ 25%]
tests/test_paths.py::test_paths_exist PASSED                             [ 26%]
tests/test_production.py::TestHealthEndpoints::test_health_check 
-------------------------------- live log call ---------------------------------
2026-01-13 19:42:42 [INFO] Request started: GET /health request_id=82e5d23b-abee-4b2b-92e4-8cd1a670a6cc client=testclient
2026-01-13 19:42:42 [INFO] Request completed: GET /health status=200 duration=0.29ms request_id=82e5d23b-abee-4b2b-92e4-8cd1a670a6cc
2026-01-13 19:42:42 [INFO] HTTP Request: GET http://testserver/health "HTTP/1.1 200 OK"
PASSED                                                                   [ 28%]
tests/test_production.py::TestHealthEndpoints::test_liveness_check 
-------------------------------- live log call ---------------------------------
2026-01-13 19:42:42 [INFO] Request started: GET /health/live request_id=2dc0c787-7067-4a39-a4c2-9bbf1b9ccd01 client=testclient
2026-01-13 19:42:42 [INFO] Request completed: GET /health/live status=200 duration=0.25ms request_id=2dc0c787-7067-4a39-a4c2-9bbf1b9ccd01
2026-01-13 19:42:42 [INFO] HTTP Request: GET http://testserver/health/live "HTTP/1.1 200 OK"
PASSED                                                                   [ 29%]
tests/test_production.py::TestHealthEndpoints::test_readiness_check 
-------------------------------- live log call ---------------------------------
2026-01-13 19:42:42 [INFO] Request started: GET /health/ready request_id=4d06bb30-6d21-4353-ac33-0cef443b5e60 client=testclient
2026-01-13 19:42:42 [INFO] Request completed: GET /health/ready status=200 duration=0.78ms request_id=4d06bb30-6d21-4353-ac33-0cef443b5e60
2026-01-13 19:42:42 [INFO] HTTP Request: GET http://testserver/health/ready "HTTP/1.1 200 OK"
PASSED                                                                   [ 30%]
tests/test_production.py::TestHealthEndpoints::test_detailed_health 
-------------------------------- live log call ---------------------------------
2026-01-13 19:42:42 [INFO] Request started: GET /health/detailed request_id=d37d1ad8-97e6-4141-bc01-48994b8b5db3 client=testclient
2026-01-13 19:42:42 [INFO] Request completed: GET /health/detailed status=200 duration=25.80ms request_id=d37d1ad8-97e6-4141-bc01-48994b8b5db3
2026-01-13 19:42:42 [INFO] HTTP Request: GET http://testserver/health/detailed "HTTP/1.1 200 OK"
PASSED                                                                   [ 32%]
tests/test_production.py::TestChatAPI::test_chat_endpoint 
-------------------------------- live log call ---------------------------------
2026-01-13 19:42:42 [INFO] Request started: POST /api/chat request_id=fe87daff-7f16-4fc1-aacc-79bb790efb4c client=testclient
2026-01-13 19:42:42 [INFO] Request completed: POST /api/chat status=200 duration=0.87ms request_id=fe87daff-7f16-4fc1-aacc-79bb790efb4c
2026-01-13 19:42:42 [INFO] HTTP Request: POST http://testserver/api/chat "HTTP/1.1 200 OK"
PASSED                                                                   [ 33%]
tests/test_production.py::TestChatAPI::test_chat_empty_message 
-------------------------------- live log call ---------------------------------
2026-01-13 19:42:42 [INFO] Request started: POST /api/chat request_id=0f7e8c73-1c53-42d6-94bf-2cf0c5de9a73 client=testclient
2026-01-13 19:42:42 [INFO] Request completed: POST /api/chat status=422 duration=0.75ms request_id=0f7e8c73-1c53-42d6-94bf-2cf0c5de9a73
2026-01-13 19:42:42 [INFO] HTTP Request: POST http://testserver/api/chat "HTTP/1.1 422 Unprocessable Entity"
PASSED                                                                   [ 34%]
tests/test_production.py::TestChatAPI::test_chat_with_rag 
-------------------------------- live log call ---------------------------------
2026-01-13 19:42:42 [INFO] Request started: POST /api/chat request_id=88c9dae7-04d0-42e8-a4e7-54b180022aa4 client=testclient
2026-01-13 19:42:42 [WARNING] SHAP explanation failed: property 'feature_names_in_' of 'Pipeline' object has no setter
2026-01-13 19:42:42 [INFO] Request completed: POST /api/chat status=200 duration=52.99ms request_id=88c9dae7-04d0-42e8-a4e7-54b180022aa4
2026-01-13 19:42:42 [INFO] HTTP Request: POST http://testserver/api/chat "HTTP/1.1 200 OK"
PASSED                                                                   [ 35%]
tests/test_production.py::TestFraudAPI::test_fraud_scoring 
-----------------
```
