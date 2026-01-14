# Sentifargo — Full Project Description
_Auto-generated on 2026-01-13 19:48:29_
## What this project is
Sentifargo (Sentifargo) is a multi-module AI platform that exposes **production-style APIs** and a **Streamlit command center UI** for anomaly/risk intelligence across multiple domains (fraud, cyber, behavior, fusion risk, RAG/document QA, recommendations, voice emotion, and computer vision including brand/logo recognition).
## High-level capabilities
- **FastAPI backend** with modular routers (chat, RAG, recommender, fraud, cyber, behavior, risk, voice, vision, brand, STT, monitoring).
- **Streamlit UI** pages for chat/command center/risk/metrics/tools/voice/brand.
- **MLOps signals**: Docker + Compose, CI workflows, metrics (Prometheus/Grafana), MLflow runs/registry patterns, explainability hooks.
- **Multimodal**: embeddings (sentence-transformers / transformers), FAISS indexing, YOLO/Ultralytics for brand/logo detection.
## Architecture at a glance
### Key entrypoints
- `app/main.py`
- `deploy/api/main.py`

### Infrastructure / Ops
**Detected:** `Dockerfile`, `Dockerfile.production`, `docker-compose.yml`, `docker-compose.production.yml`, `Makefile`, `pyproject.toml`, `requirements.txt`

**GitHub Actions workflows:**
- `.github/workflows/ci-cd.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/deploy-pages.yml`

## API surface summary (FastAPI)
- **Total detected endpoints:** **51**

**Endpoint groups (approx):**
- `/health*`: 6
- `predict`: 3
- `recommend`: 3
- ``: 2
- `events`: 2
- `multimodal`: 2
- `summary`: 2
- `/api/*`: 1
- `/metrics*`: 1
- `analyze`: 1
- `baseline`: 1
- `chat`: 1

**Sample endpoints (first 30):**
- `GET` `/api/health`  — `app/main.py`
- `GET` `/`  — `app/main.py`
- `GET` `/health`  — `app/core/health.py`
- `GET` `/health/live`  — `app/core/health.py`
- `GET` `/health/ready`  — `app/core/health.py`
- `GET` `/health/detailed`  — `app/core/health.py`
- `GET` `/metrics`  — `app/core/health.py`
- `GET` `/ready`  — `app/core/health.py`
- `GET` `/events`  — `app/api/cyber_timeline.py`
- `GET` `/patterns`  — `app/api/cyber_timeline.py`
- `GET` `/sources`  — `app/api/cyber_timeline.py`
- `GET` `/summary`  — `app/api/cyber_timeline.py`
- `POST` `/log`  — `app/api/monitor.py`
- `GET` `/summary`  — `app/api/monitor.py`
- `GET` `/drift`  — `app/api/monitor.py`
- `GET` `/risk_summary`  — `app/api/monitor.py`
- `GET` `/events`  — `app/api/monitor.py`
- `POST` `/baseline/build`  — `app/api/monitor.py`
- `GET` `/health`  — `app/api/health.py`
- `POST` `/predict`  — `app/api/vision_temporal.py`
- `POST` `/speak`  — `app/api/tts.py`
- `POST` `/fraud`  — `app/api/fraud.py`
- `POST` `/emotion`  — `app/api/voice.py`
- `POST` `/chat`  — `app/api/chat.py`
- `POST` `/ingest`  — `app/api/rag.py`
- `POST` `/upload`  — `app/api/rag.py`
- `POST` `/analyze`  — `app/api/fusion.py`
- `POST` `/risk/analyze`  — `app/api/risk.py`
- `POST` `/predict`  — `app/api/brand.py`
- `POST` `/recommend`  — `app/api/recommender.py`

## Streamlit UI
**Pages found:**
- `app/streamlit_chatbot/pages/__init__.py`
- `app/streamlit_chatbot/pages/brand.py`
- `app/streamlit_chatbot/pages/chat.py`
- `app/streamlit_chatbot/pages/command_center.py`
- `app/streamlit_chatbot/pages/live.py`
- `app/streamlit_chatbot/pages/metrics.py`
- `app/streamlit_chatbot/pages/risk.py`
- `app/streamlit_chatbot/pages/tools.py`
- `app/streamlit_chatbot/pages/voice_chat.py`

## Training / pipelines
**Trainer / pipeline scripts detected:**
- `scripts/train_all.py`
- `scripts/train_all_vision.py`
- `scripts/train_all_vision_full.py`
- `scripts/train_production.py`
- `src/pipeline/build_features.py`
- `src/pipeline/ingest.py`
- `src/pipeline/train_models.py`
- `src/train/__init__.py`
- `src/train/train_behavior.py`
- `src/train/train_brand_logo_detector.py`
- `src/train/train_cyber.py`
- `src/train/train_face_emotion.py`
- `src/train/train_fraud.py`
- `src/train/train_fusion.py`
- `src/train/train_movielens_recommender.py`
- `src/train/train_recommender.py`
- `src/train/train_video_temporal.py`

## Data layout (top-level)
**`data/` contains:**
- `data/catalogs`
- `data/Celeb_V2`
- `data/docs`
- `data/embeddings`
- `data/interim`
- `data/monitoring`
- `data/processed`
- `data/raw`
- `data/README.md`
- `data/synthetic`
- `data/Video-2`

## Existing documentation excerpts
## Excerpt: EXECUTIVE_SUMMARY.md

**Source:** `EXECUTIVE_SUMMARY.md`

```text
# Sentifargo - Executive Summary

## One-Liner
**Sentifargo** is an AI-powered anomaly detection platform combining fraud detection, cybersecurity analysis, and intelligent recommendations in a single offline-capable system.

---

## 🎯 What It Does

| Feature | Description |
|---------|-------------|
| **Fraud Detection** | 99.2% accurate ML model detecting suspicious transactions |
| **Cyber Threat Analysis** | Network anomaly detection using Isolation Forest |
| **Smart Recommendations** | 60K+ movies with personalized suggestions |
| **Vision Analysis** | 154K+ images for authenticity detection |
| **Intelligent Chat** | 50+ varied responses without requiring APIs |

---

## 🛠️ Tech Stack

**Backend**: Python 3.13, FastAPI, PyTorch, scikit-learn, XGBoost  
**Frontend**: React 18, TypeScript, Tailwind CSS  
**ML**: Random Forest, Isolation Forest, CNN, TF-IDF  
**Data**: 154K images, 60K movies, 100K transactions  

---

## 💡 Key Innovation

**Offline-First AI** - Unlike typical chatbots requiring OpenAI/cloud APIs:
- All ML models run locally
- 50+ intelligent response variations
- Zero external API dependencies
- Sub-second response times

---

## 📊 By The Numbers

| Metric | Value |
|--------|-------|
| Python Files | 352 |
| Lines of Code | ~50,000 |
| ML Models | 6 |
| Training Images | 154,000+ |
| Movie Database | 60,000+ |
| Fraud Accuracy | 99.2% |

---

## 🚀 Quick Demo

```bash
# Start server
uvicorn app.main:app --port 8000

# Test chat
curl -X POST http://localhost:8000/api/chat \
  -d '{"text": "recommend action movies"}'

# Response: Different movies every time!
```

---

## 📁 Architecture

```
User → FastAPI → Orchestrator → ML Models → Response
                      ↓
         [Fraud | Cyber | Vision | NLP | Recommender]
```

---

## 🎓 Skills Demonstrated

- Machine Learning Engineering
- Full-Stack Development (Python + React)
```
## Excerpt: PROJECT_SUMMARY.md

**Source:** `PROJECT_SUMMARY.md`

```text
# Sentifargo: Sentifargo

## 🎯 Project Overview

**Sentifargo** is a comprehensive AI-powered anomaly detection and intelligent recommendation platform built by **Pratik Niroula** as part of the CIS 380 course project. The system demonstrates practical applications of machine learning in security, fraud detection, and personalized recommendations.

### Key Highlights
- **154,000+ images** processed for vision analysis
- **60,000+ movies** in the recommendation database
- **99.2% accuracy** in fraud detection
- **6 ML models** integrated (fraud, cyber, behavior, vision, NLP, fusion)
- **100% offline capable** - works without external APIs

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   React/TS UI   │  │  Streamlit App  │  │  GitHub Pages   │ │
│  │  (Command Ctr)  │  │   (Chat/Demo)   │  │   (Portfolio)   │ │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘ │
└───────────┼─────────────────────┼─────────────────────┼─────────┘
            │                     │                     │
            ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   API Routes                             │   │
│  │  /api/chat  │  /api/risk  │  /api/vision  │  /api/voice │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                    │
│  ┌─────────────────────────┴─────────────────────────────┐     │
│  │              Sentifargo Orchestrator               │     │
│  │   • Intent Detection  • Route Selection  • Response   │     │
│  └───────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ML Models Layer                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  Fraud   │ │  Cyber   │ │ Behavior │ │  Vision  │           │
│  │ Detection│ │ Threat   │ │ Analysis │ │ Analysis │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────────┐            │
│  │   NLP    │ │  Fusion  │ │    Recommender       │            │
│  │ Analysis │ │  Model   │ │  (Movies/Products)   │            │
│  └──────────┘ └──────────┘ └──────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  RAG Store  │  │  Catalogs   │  │  Training Datasets      │ │
│  │  (Docs/QA)  │  │  (Items)    │  │  (Fraud/Cyber/Vision)   │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔥 Core Features

### 1. Fraud Detection System
- **Model**: XGBoost/Random Forest ensemble
- **Accuracy**: 99.2% on test data
- **Features**: Transaction amount, velocity, location, device fingerprinting
- **Real-time**: Sub-second prediction latency
- **Explainability**: SHAP values for feature importance

### 2. Cybersecurity Threat Analysis
- **Detection Types**: Network intrusion, anomalous patterns
- **Methods**: Isolation Forest, LSTM for sequence analysis
- **Metrics**: Precision, recall, F1-score tracking
- **Alerts**: Configurable threshold-based alerting
```
## Excerpt: PROJECT_DOCUMENTATION.md

**Source:** `PROJECT_DOCUMENTATION.md`

```text
# Sentifargo (Sentifargo)
## Complete Project Documentation

**Author:** Pratik Niroula  
**Project:** CIS 380 - Machine Learning & Anomaly Detection  
**Last Updated:** January 2026

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Directory Structure](#directory-structure)
3. [Core Components](#core-components)
4. [How Each Module Works](#how-each-module-works)
5. [Running the Project](#running-the-project)
6. [API Endpoints](#api-endpoints)
7. [File-by-File Documentation](#file-by-file-documentation)

---

## 🎯 Project Overview

### What is Sentifargo?

Sentifargo (Sentifargo) is a **multi-modal machine learning platform** that detects various types of anomalies:

| Module | What It Detects | Use Case |
|--------|-----------------|----------|
| **Fraud** | Financial fraud | Credit card transactions, payment anomalies |
| **Cyber** | Network intrusions | Malicious traffic, DDoS attacks |
| **Behavior** | Insider threats | Unusual user activity patterns |
| **Vision** | Fake images | Deepfakes, manipulated photos |
| **NLP** | Text anomalies | Spam, malicious content |
| **Voice** | Audio emotions | Sentiment in voice recordings |

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                          │
│                     ui-web/frontend/src/                         │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                             │
│                        app/main.py                               │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐      │
│  │  /fraud  │  /cyber  │ /behavior│ /vision  │   /rag   │      │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘      │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ML MODELS (src/uais/)                        │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐      │
│  │  XGBoost │ RandomF  │   LSTM   │   CNN    │  BERT    │      │
│  │  (Fraud) │ (Cyber)  │(Behavior)│ (Vision) │  (NLP)   │      │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Directory Structure

```
Sentifargo/
│
├── app/                          # FastAPI application
│   ├── main.py                   # 🔑 Main entry point - starts the API server
│   ├── api/                      # API route handlers
│   │   ├── risk.py              # Unified risk scoring endpoint
│   │   ├── voice.py             # Voice emotion analysis
│   │   ├── brand.py             # Brand/logo detection
│   │   └── ...
│   ├── core/                     # Core utilities
│   │   ├── config.py            # Configuration management
│   │   ├── logging.py           # Logging setup
```
## Excerpt: PROJECT_AUDIT_REPORT.md

**Source:** `PROJECT_AUDIT_REPORT.md`

```text
# 📊 PROJECT AUDIT REPORT

## 📁 Repository Structure
.
./ui-web
./ui-web/frontend
./ui-web/frontend/dist
./ui-web/frontend/dist/assets
./ui-web/frontend/node_modules
./ui-web/frontend/node_modules/queue-microtask
./ui-web/frontend/node_modules/tinyglobby
./ui-web/frontend/node_modules/@alloc
./ui-web/frontend/node_modules/reusify
./ui-web/frontend/node_modules/jsesc
./ui-web/frontend/node_modules/pirates
./ui-web/frontend/node_modules/@types
./ui-web/frontend/node_modules/browserslist
./ui-web/frontend/node_modules/thenify
./ui-web/frontend/node_modules/.bin
./ui-web/frontend/node_modules/jiti
./ui-web/frontend/node_modules/csstype
./ui-web/frontend/node_modules/path-type
./ui-web/frontend/node_modules/@rolldown
./ui-web/frontend/node_modules/make-dir
./ui-web/frontend/node_modules/pkg-dir
./ui-web/frontend/node_modules/loose-envify
./ui-web/frontend/node_modules/es-errors
./ui-web/frontend/node_modules/sucrase
./ui-web/frontend/node_modules/ms
./ui-web/frontend/node_modules/filenamify
./ui-web/frontend/node_modules/math-intrinsics
./ui-web/frontend/node_modules/node-releases
./ui-web/frontend/node_modules/escape-string-regexp
./ui-web/frontend/node_modules/has-tostringtag
./ui-web/frontend/node_modules/mz
./ui-web/frontend/node_modules/lru-cache
./ui-web/frontend/node_modules/commander
./ui-web/frontend/node_modules/autoprefixer
./ui-web/frontend/node_modules/escalade
./ui-web/frontend/node_modules/postcss-load-config
./ui-web/frontend/node_modules/path-exists
./ui-web/frontend/node_modules/resolve
./ui-web/frontend/node_modules/call-bind-apply-helpers
./ui-web/frontend/node_modules/trim-repeated
./ui-web/frontend/node_modules/object-hash
./ui-web/frontend/node_modules/nanoid
./ui-web/frontend/node_modules/ts-interface-checker
./ui-web/frontend/node_modules/@nodelib
./ui-web/frontend/node_modules/postcss-js
./ui-web/frontend/node_modules/gensync
./ui-web/frontend/node_modules/proxy-from-env
./ui-web/frontend/node_modules/ignore
./ui-web/frontend/node_modules/picomatch
./ui-web/frontend/node_modules/function-bind
./ui-web/frontend/node_modules/is-glob
./ui-web/frontend/node_modules/typescript
./ui-web/frontend/node_modules/baseline-browser-mapping
./ui-web/frontend/node_modules/jsonfile
./ui-web/frontend/node_modules/dir-glob
./ui-web/frontend/node_modules/anymatch
./ui-web/frontend/node_modules/es-define-property
./ui-web/frontend/node_modules/async
./ui-web/frontend/node_modules/chokidar
./ui-web/frontend/node_modules/postcss
./ui-web/frontend/node_modules/p-locate
./ui-web/frontend/node_modules/@rollup
./ui-web/frontend/node_modules/get-intrinsic
./ui-web/frontend/node_modules/email-addresses
./ui-web/frontend/node_modules/arg
./ui-web/frontend/node_modules/commondir
./ui-web/frontend/node_modules/scheduler
./ui-web/frontend/node_modules/pify
./ui-web/frontend/node_modules/gh-pages
./ui-web/frontend/node_modules/is-binary-path
./ui-web/frontend/node_modules/combined-stream
./ui-web/frontend/node_modules/dunder-proto
./ui-web/frontend/node_modules/hasown
./ui-web/frontend/node_modules/run-parallel
./ui-web/frontend/node_modules/p-limit
./ui-web/frontend/node_modules/@remix-run
```
## Excerpt: README.md

**Source:** `README.md`

```text
# Sentifargo# Sentifargo# Sentifargo



[![CI](https://github.com/Pratikn03/Cis380/actions/workflows/ci.yml/badge.svg)](https://github.com/Pratikn03/Cis380/actions/workflows/ci.yml)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)**Sentifargo** is a comprehensive risk intelligence platform for fraud detection, cybersecurity monitoring, and behavioral analytics.Sentifargo is a **multimodal AI agent platform** that routes a single user request to the right subsystem (RAG, fraud/cyber/behavior scoring, recommendations, voice emotion, vision) and returns a **single structured response**: `{"route", "answer", "meta"}`.

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)



**Sentifargo** is a **production-grade multimodal AI platform** for enterprise anomaly detection, combining fraud detection, cybersecurity monitoring, behavioral analytics, voice emotion analysis, and computer vision into a unified intelligence system.

## 🌐 Live DemoThe goal of this repository is not “a chatbot in a notebook”, but an end-to-end system that looks and feels like a service: **API, UI, training, monitoring, and a repeatable test gate**.

## 🌐 Live Demo



**[View Live Demo →](https://pratikn03.github.io/Cis380/)**

**[View Live Demo →](https://pratikn03.github.io/Cis380/)**## What You Get

## ✨ Key Features

- **FastAPI gateway** (`uvicorn app.main:app`) that mounts chat + RAG + risk + recommender + vision + monitoring endpoints.

| Domain | Capabilities |

|--------|-------------|## Features- **Streamlit command center UI** (`streamlit run app/streamlit_chatbot/app.py`) with chat, multimodal uploads, and dashboards.

| **Fraud Detection** | Transaction scoring, velocity analysis, synthetic fraud generation |

| **Cybersecurity** | Network intrusion detection (UNSW-NB15), attack timeline visualization |- **Offline-first behavior** by default (local models + local RAG). Add `OPENAI_API_KEY` to enable LLM chat/streaming.

| **Behavior Analytics** | User session modeling, insider threat detection, anomaly scoring |

| **Voice Intelligence** | Emotion recognition, stress detection, speech-to-text |- **Risk Analysis** - Real-time fraud and cyber threat detection- **Training entrypoints** for core models + optional vision/YOLO/face-emotion (`scripts/train_all.py`, `src/train/*`).

| **Computer Vision** | Image classification, video analysis, facial emotion, brand detection |

| **RAG System** | Document ingestion, semantic search, multi-strategy chunking |- **Behavioral Monitoring** - User behavior pattern analysis- **Monitoring + drift summaries** with Prometheus metrics (`/metrics`) and JSONL event logs under `data/monitoring/logs/`.

| **Recommendations** | Collaborative filtering, multimodal similarity (MovieLens) |

- **Voice Analytics** - Emotion detection from audio

## 🏗️ Architecture

- **Vision Processing** - Image and video analysis for security## Architecture (At a Glance)

```

┌─────────────────────────────────────────────────────────────────────────┐- **Dashboard** - Interactive command center UI

│                         Sentifargo Platform                          │

├─────────────────────────────────────────────────────────────────────────┤```mermaid

│  Layer 1: Interface                                                     │

│  ├── Streamlit UI (app/streamlit_chatbot/)                              │## Architectureflowchart TD

│  ├── React Frontend (ui-web/frontend/)                                  │

│  └── REST API (FastAPI)                                                 │  UI[Streamlit UI] --> API[FastAPI Gateway]

├─────────────────────────────────────────────────────────────────────────┤

│  Layer 2: Orchestration                                                 │```  API --> ORCH[Orchestrator]

│  └── Intent Router → Domain Routing → Response Fusion                   │

├─────────────────────────────────────────────────────────────────────────┤┌─────────────────────────────────────────────────────────────┐  ORCH --> RAG[RAG (data/docs + embeddings)]

│  Layer 3: Intelligence Engines                                          │
```
## Excerpt: ARCHITECTURE.md

**Source:** `docs/ARCHITECTURE.md`

```text
# 🏗️ Sentifargo Architecture

**Version:** 2.0  
**Last Updated:** January 8, 2026

---

## 📐 System Architecture Diagram

```
┌────────────────────────────┐
│        Frontend UI         │
│  React (Web) / Streamlit   │
│  ChatGPT-style Interface   │
└─────────────┬──────────────┘
              │ REST / JSON
┌─────────────▼──────────────┐
│        FastAPI API         │
│  Auth • Rate-limit • Logs  │
└─────────────┬──────────────┘
              │
┌─────────────▼──────────────┐
│   Agent / Orchestrator     │
│ Intent • Routing • Memory  │
└─────────────┬──────────────┘
              │
┌─────────────▼────────────────────────────────────────────┐
│                  Model Services Layer                     │
│                                                           │
│ Fraud │ Cyber │ Behavior │ Vision │ Audio │ NLP │ RAG    │
│ (Tab) │ (Seq) │ (Time)   │ (Img/V)│ (STT) │(Text)│       │
└─────────────┬────────────────────────────────────────────┘
              │
┌─────────────▼──────────────┐
│     Multimodal Fusion      │
│ Meta-Model + Rule Engine   │
│ Risk Score + Decision      │
└─────────────┬──────────────┘
              │
┌─────────────▼──────────────┐
│ Monitoring & Explainability│
│ Drift • SHAP • Metrics     │
└─────────────┬──────────────┘
              │
┌─────────────▼──────────────┐
│        MLOps Stack         │
│ MLflow • DVC • Registry    │
│ Auto-Retrain • CI/CD       │
└─────────────┬──────────────┘
              │
┌─────────────▼──────────────┐
│     Infra & Deployment     │
│ Docker • Nginx • Grafana   │
│ Prometheus • Redis         │
└────────────────────────────┘
```

---

## 🗂️ Layer-by-Layer Breakdown

### 1️⃣ Frontend UI Layer

| Component | Technology | Location |
|-----------|------------|----------|
| Web Interface | React + TypeScript + Tailwind | `ui-web/frontend/` |
| Dashboard | Streamlit | `dashboard/app_streamlit.py` |
| Chat Interface | React Chat Component | `ui-web/frontend/src/pages/Chat.tsx` |
| Result Cards | React Component | `ui-web/frontend/src/components/ResultCard.tsx` |
| File Upload | React Component | `ui-web/frontend/src/components/UnifiedUploadBox.tsx` |

**Features:**
- ChatGPT-style conversational interface
- Real-time streaming responses
- Multimodal input (text, images, audio, documents)
- Confidence visualization bars
- SHAP explainability dashboard

---
```
## Excerpt: MLOPS_ROADMAP.md

**Source:** `docs/MLOPS_ROADMAP.md`

```text
# MLOps Roadmap: Shadow Mode & Model Updates

## Overview

This document outlines the MLOps roadmap for Sentifargo, including shadow mode deployment, model validation, and safe rollout strategies.

## Current MLOps Stack

| Component | Status | Technology |
|-----------|--------|------------|
| Model Registry | ✅ Implemented | `src/mlops/registry.py` + MLflow |
| Experiment Tracking | ✅ Implemented | MLflow |
| Data Versioning | ✅ Implemented | DVC |
| Confidence Scoring | ✅ Implemented | `src/mlops/confidence.py` |
| A/B Testing | ✅ Implemented | `src/mlops/ab_testing.py` |
| Latency Monitoring | ✅ Implemented | `app/monitoring/latency.py` |
| Audit Logging | ✅ Implemented | `src/mlops/audit_logger.py` |

## Shadow Mode Architecture

### What is Shadow Mode?

Shadow mode runs a new model version in parallel with production, comparing predictions without affecting users. This enables:

1. **Safe validation** - Test new models on real traffic
2. **Performance comparison** - Compare latency, accuracy, drift
3. **Gradual rollout** - Increase traffic percentage over time
4. **Instant rollback** - Switch back without deployment

### Implementation Plan

#### Phase 1: Shadow Infrastructure (Q2 2024)

```
┌─────────────────────────────────────────────────────────┐
│                     Request                              │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                  Traffic Router                          │
│  ┌───────────────┐     ┌───────────────────────────┐   │
│  │ Production    │     │ Shadow (async)             │   │
│  │ Model v1.2    │     │ Model v1.3-candidate       │   │
│  │ (100% serve)  │     │ (100% mirror, 0% serve)    │   │
│  └───────┬───────┘     └───────────────┬───────────┘   │
│          │                             │                │
│          ▼                             ▼                │
│    User Response              Shadow Metrics            │
│                               (logged only)             │
└─────────────────────────────────────────────────────────┘
```

**Files to create:**
- `src/mlops/shadow_mode.py` - Shadow routing logic
- `src/mlops/shadow_metrics.py` - Comparison metrics
- `app/api/routes/shadow.py` - Shadow management API

#### Phase 2: Comparison Dashboard (Q2 2024)

Compare shadow vs production on:
- Prediction distribution differences
- Latency percentiles (p50, p95, p99)
- Confidence score calibration
- Feature importance shifts
- Error rate by input type

**Files to create:**
- `dashboard/components/shadow_comparison.py` - Streamlit component
- `reports/shadow/` - Generated comparison reports

#### Phase 3: Automated Promotion (Q3 2024)

Automated promotion criteria:
```python
PROMOTION_CRITERIA = {
    "min_shadow_duration_hours": 168,  # 1 week
    "min_request_count": 10000,
    "max_prediction_drift": 0.05,  # KL divergence
    "max_latency_increase_pct": 10,
```
## Excerpt: LEGACY.md

**Source:** `docs/LEGACY.md`

```text
# Legacy Code Documentation

## Overview

Sentifargo evolved from multiple iterations of the codebase. This document explains what's legacy, what's current, and the deprecation roadmap.

## Architecture Evolution

```
v0.1 (Original)     v0.2 (Refactored)     v1.0 (Current)
----------------    ------------------    ----------------
backend/            app/legacy/           app/
api/                app/legacy/api/       app/api/
agent/              app/legacy/agent/     app/services/
rag/                app/legacy/rag/       app/rag/
```

## Current vs Legacy Mapping

### ✅ Current (Preferred)

| Component | Location | Status |
|-----------|----------|--------|
| Main API | `app/main.py` | ✅ Active |
| Chat API | `app/api/routes/chat.py` | ✅ Active |
| RAG Service | `app/rag/` | ✅ Active |
| Streamlit UI | `app/streamlit_chatbot/` | ✅ Active |
| Monitoring | `app/monitoring/` | ✅ Active |
| ML Services | `app/services/` | ✅ Active |

### ⚠️ Legacy (Deprecated)

| Component | Location | Reason | Migration Path |
|-----------|----------|--------|----------------|
| Legacy API Routes | `app/legacy/api/routes/` | Older endpoint structure | Use `/api/*` routes |
| Legacy Orchestrator | `app/legacy/agent/orchestrator.py` | Type issues, tightly coupled | Use `app/services/` |
| Legacy RAG | `app/legacy/rag/` | Older vector store implementation | Use `app/rag/` |
| Legacy Chat Responses | `app/legacy/agent/chat_responses.py` | Hardcoded responses | Use orchestrator |

### 🗑️ Deprecated (To Remove)

| Component | Location | Target Removal |
|-----------|----------|----------------|
| Old backend | `backend/main.py` | v2.0 |
| Standalone API | `api/routes/` | v2.0 |
| Old agent | `agent/orchestrator.py` | v2.0 |

## Why Legacy Code Exists

### 1. Backwards Compatibility

The legacy routes (`app/legacy/api/routes/`) are still mounted in `app/main.py` for backwards compatibility:

```python
# app/main.py
from app.legacy.api.routes import behavior, chat, cyber, fraud, rag, recommend, vision

# Legacy routers (no authentication required for demo)
app.include_router(fraud.router, prefix="/api/fraud", tags=["fraud"])
app.include_router(cyber.router, prefix="/api/cyber", tags=["cyber"])
```

### 2. Demo/Testing

Some legacy endpoints are simpler and useful for quick testing without authentication.

### 3. Migration In Progress

Some components are being migrated incrementally:
- RAG: Legacy uses TF-IDF, current uses embeddings
- Chat: Legacy has hardcoded responses, current uses orchestrator

## Type Issues in Legacy Code

The legacy orchestrator has known type issues (reported by pyright/mypy):

```python
# app/legacy/agent/orchestrator.py
# Known issues:
# - Mixed DataFrame/ndarray handling
```
