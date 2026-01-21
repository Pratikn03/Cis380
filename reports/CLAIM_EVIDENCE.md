# Claim Evidence Report

Generated: 2026-01-15 14:14:10

## C1. Orchestrator routes a single request to the right subsystem

- Status: PROVEN
- Evidence:
  - app/agent/orchestrator.py - app/agent/orchestrator.py:53: route = self.decision_engine.decide_route(
  - app/agent/orchestrator.py - app/agent/orchestrator.py:147: def _invoke_route(
  - app/agent/orchestrator.py - app/agent/orchestrator.py:160: def _run_rag(self, text: str, emotion: dict[str, Any] | None) -> tuple[str, Dict[str, Any]]:
  - app/agent/orchestrator.py - app/agent/orchestrator.py:181: def _run_fraud(self, text: str) -> tuple[str, Dict[str, Any]]:
  - app/agent/orchestrator.py - app/agent/orchestrator.py:193: def _run_voice(self, text: str) -> tuple[str, Dict[str, Any]]:
  - app/api/chat.py - app/api/chat.py:8: from app.agent import MemoryStore, SentifargoOrchestrator
  - app/api/chat.py - app/api/chat.py:12: orchestrator = SentifargoOrchestrator(llm_client=LLMStub(), memory_store=MemoryStore.from_env())
  - app/api/chat.py - app/api/chat.py:24: return orchestrator.handle(
- Notes:
  - Import check: app.agent.orchestrator ok

## C2. MLflow registry patterns

- Status: PARTIAL
- Evidence:
  - src/uais/utils/mlflow_utils.py - src/uais/utils/mlflow_utils.py:33: mlflow.set_tracking_uri(uri)
  - src/uais/utils/mlflow_utils.py - src/uais/utils/mlflow_utils.py:34: mlflow.set_experiment(experiment_name)
  - src/uais/utils/mlflow_utils.py - src/uais/utils/mlflow_utils.py:40: mlflow.set_tracking_uri(local_uri.as_uri())
  - src/uais/utils/mlflow_utils.py - src/uais/utils/mlflow_utils.py:41: mlflow.set_experiment(experiment_name)
  - mlflow_config.yaml - mlflow_config.yaml exists
  - app/mlops/registry.py - app/mlops/registry.py:96: class ModelRegistry:
  - app/mlops/registry.py - app/mlops/registry.py:158: def register_model(

## C3. DVC implemented

- Status: PROVEN
- Evidence:
  - dvc.yaml - dvc.yaml exists
  - dvc.yaml - dvc.yaml:5: stages:
  - dvc.yaml - dvc.yaml:6: train_fraud_model:
  - dvc.yaml - dvc.yaml:64: evaluate_all:
  - dvc.yaml - dvc.yaml:65: cmd: PYTHONPATH=src python -m uais.evaluation.evaluate_all
  - dvc.yaml - dvc.yaml:67: - src/uais/evaluation/evaluate_all.py
  - dvc.lock - dvc.lock exists

## C4. Offline-first

- Status: PROVEN
- Evidence:
  - app/rag_dsa/config.py - app/rag_dsa/config.py:11: ONLINE_MODE = os.getenv("DSA_ONLINE_MODE", "false").lower() == "true"
  - app/rag_dsa/online.py - app/rag_dsa/online.py:26: def online_enabled() -> bool:
  - app/rag_dsa/online.py - app/rag_dsa/online.py:27: return settings.ONLINE_MODE and bool(settings.OPENAI_API_KEY)
  - app/rag_dsa/embeddings.py - app/rag_dsa/embeddings.py:6: from sklearn.feature_extraction.text import HashingVectorizer
  - app/rag_dsa/embeddings.py - app/rag_dsa/embeddings.py:12: """Offline-safe embedding model using HashingVectorizer."""
  - app/rag_dsa/embeddings.py - app/rag_dsa/embeddings.py:16: self.model = HashingVectorizer(
  - app/utils/llm_stub.py - offline LLM stub present

## C5. Prometheus/Grafana

- Status: PROVEN
- Evidence:
  - deploy/prometheus/prometheus.yml - prometheus.yml exists
  - deploy/grafana/provisioning/datasources/datasource.yml - grafana datasource exists
  - docker-compose.production.yml - docker-compose.production.yml:124: prometheus:
  - docker-compose.production.yml - docker-compose.production.yml:125: image: prom/prometheus:v2.47.0
  - docker-compose.production.yml - docker-compose.production.yml:146: grafana:
  - docker-compose.production.yml - docker-compose.production.yml:147: image: grafana/grafana:10.2.0
  - app/core/health.py - app/core/health.py:21: from prometheus_client import (
  - app/core/health.py - app/core/health.py:526: @router.get("/metrics")
  - app/core/health.py - app/core/health.py:527: async def prometheus_metrics() -> Response:

## C6. 99.2% fraud accuracy

- Status: MISSING
- Evidence:
  - reports/evaluation_summary.json - metrics file exists
  - reports/model_comparison.json - metrics file exists
  - ui-web/frontend/src/pages/Home.tsx - ui-web/frontend/src/pages/Home.tsx:70: Building intelligent systems that detect anomalies, prevent fraud, and secure digital infrastructure through advanced machine learning.
  - ui-web/frontend/src/pages/Home.tsx - ui-web/frontend/src/pages/Home.tsx:97: { value: "99.2%", label: "Detection Accuracy" },
  - ui-web/frontend/src/pages/Home.tsx - ui-web/frontend/src/pages/Home.tsx:144: desc: "Multi-modal ensemble combining all detection engines for superior accuracy",
  - ui-web/frontend/src/pages/CommandCenter.tsx - ui-web/frontend/src/pages/CommandCenter.tsx:4: { label: "Detection Accuracy", value: "99.2%" },
  - ui-web/frontend/src/pages/CommandCenter.tsx - ui-web/frontend/src/pages/CommandCenter.tsx:53: Sentifargo is a comprehensive AI-powered anomaly detection and intelligent recommendation platform built by Pratik Niroula as part of the CIS 380 course project. The system demonstrates practical applications of machine learning in security, fraud detection, and personalized recommendations.
  - ui-web/frontend/src/pages/CommandCenter.tsx - ui-web/frontend/src/pages/CommandCenter.tsx:58: - 99.2% accuracy in fraud detection
  - ui-web/frontend/src/pages/CommandCenter.tsx - ui-web/frontend/src/pages/CommandCenter.tsx:59: - 6 ML models integrated (fraud, cyber, behavior, vision, NLP, fusion)
  - ui-web/frontend/src/pages/CommandCenter.tsx - ui-web/frontend/src/pages/CommandCenter.tsx:79: - Training datasets (fraud, cyber, vision)
  - docs/PROJECT_DESCRIPTION.md - docs/PROJECT_DESCRIPTION.md:4: Sentifargo (Sentifargo) is a multi-module AI platform that exposes **production-style APIs** plus a **Streamlit command center UI** and a **React web UI** for anomaly/risk intelligence across multiple domains (fraud, cyber, behavior, fusion risk, RAG/document QA, recommendations, voice emotion, computer vision including brand/logo recognition, and offline-first DSA RAG with optional online fallback).
  - docs/PROJECT_DESCRIPTION.md - docs/PROJECT_DESCRIPTION.md:6: - **FastAPI backend** with modular routers (chat, RAG, recommender, fraud, cyber, behavior, risk, voice, vision, brand, STT, monitoring).
  - docs/PROJECT_DESCRIPTION.md - docs/PROJECT_DESCRIPTION.md:101: - Measurable claims (accuracy/latency/cost) backed by scripts + reports.
  - docs/PROJECT_DESCRIPTION.md - docs/PROJECT_DESCRIPTION.md:102: - Evaluation harness across modules (fraud/cyber/vision/voice/RAG) + regression tests.
  - docs/PROJECT_DESCRIPTION.md - docs/PROJECT_DESCRIPTION.md:126: - Build a full evaluation harness across fraud/cyber/vision/voice/RAG with regression tests.
- Notes:
  - No metrics artifact with 99.2/0.992 found in reports
  - Claim appears in UI/docs copy; consider linking to a metrics file
