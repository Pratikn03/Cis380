# Project Audit Report (2026-01-29)

Scope: full repository audit with a deep dive on voice emotion detection (speech).  
Method: static code review + dataset header scan for voice WAVs + artifact/log inspection.

---

## 1) Executive Summary

This repo is a large multi‑domain ML system (fraud, cyber, behavior, vision, voice, RAG, recommender) with extensive scripts, notebooks, and deployment assets. The voice emotion system is functional but **not world‑class**: it uses small acted data and a lightweight MFCC + RandomForest model with ~54% accuracy, which is far below elite performance. The current dataset is ~7.4k clips (≈592MB), uniformly 16kHz, acted, short (≈2–3s) and is **insufficient** for real‑world emotion or crying detection at the “99% accuracy / 0.5% error” level.

**Top priorities:**
1) Upgrade voice emotion model to a modern SSL encoder (Wav2Vec2/HubERT/WavLM) and add real‑world emotion/crying datasets.
2) Enforce speaker‑independent splits and track WER/CER for STT; avoid leakage.
3) Formalize MLOps pipeline: data versioning, evaluation, and model registry for every domain.
4) Security hardening: ensure no secrets in git, tighten CORS/allowed hosts for production.

---

## 2) Repository Inventory (High Level)

**Core services**
- API: `app/` (FastAPI), endpoints across modules (`app/api/*`)
- Streamlit apps: `app/streamlit_chatbot/`
- MLOps + training: `scripts/`, `src/train/`, `scripts/train_production.py`, `scripts/retrain_all_98.py`
- Models & artifacts: `models/`, `artifacts/`
- Datasets: `data/raw/*`, DVC config (`dvc.yaml`, `.dvc/`)
- CI/CD: `.github/workflows/*`
- Docker / deployment: `docker-compose*.yml`, `deploy/`, `Dockerfile*`
- Frontend: `ui-web/`

**Tests**
- 37 test files in `tests/` (API endpoints, voice, vision, security, etc.)
- Pytest config in `pytest.ini` with optional plugins.

---

## 3) Data & Dataset Health

### 3.1 Voice Emotion Dataset (current)
Location: `data/raw/voice/`  
Size: **~592MB**  
Classes: angry / happy / neutral / sad / fearful  

Header scan (WAV only):
- All files at **16kHz**
- Durations (mean): **2.34–2.68s**
- All 5 classes share the same **91 speakers**

Counts:
- angry: 2,542  
- happy: 1,271  
- neutral: 1,087  
- sad: 1,270  
- fearful: 1,271  
Total: **7,441** clips

**Implications:**  
This looks like CREMA‑D (acted speech), which is not sufficient for real‑world emotion or crying detection. The dataset is short‑utterance, clean, and acted. It will not generalize to spontaneous speech, noisy environments, children, non‑studio recordings, or real crying.

### 3.2 STT Dataset (current)
Location: `data/raw/stt/` (manifests only)  
Files: `manifest.train.csv`, `manifest.val.csv`, `manifest.test.csv`, `manifest.csv`  
Note: STT manifests exist but training has been unstable on MPS. Model training logs are in `reports/whisper_large/`.

---

## 4) Voice Emotion Pipeline (Deep Audit)

### 4.1 Training
File: `app/models/voice/emotion_train.py`  
Model: `RandomForestClassifier` with `StandardScaler`  
Features: 26 MFCC + ZCR + RMS + pitch + spectral contrast (31 features)

Latest training log (`reports/voice_emotion_train.log`):
- **Accuracy: 54.06%**

### 4.2 Inference
File: `app/models/voice/emotion_predict.py`  
Endpoint: `app/api/voice.py` at `POST /api/voice/emotion`
- Accepts WAV/Audio
- Uses MFCC + hand‑crafted features
- Provides per‑segment heuristics

### 4.3 Gaps vs World‑Class Emotion Detection
1) **Data scale + realism**: 7.4k acted clips ≠ real-world.
2) **Label taxonomy**: “crying” is not a class; current labels are generic acted emotions.
3) **Model capacity**: MFCC + RandomForest is not competitive with SSL encoders.
4) **Evaluation leakage risk**: current split is random, not speaker‑independent.
5) **Metrics**: only accuracy; no macro‑F1, UAR, confusion matrix, or per‑speaker performance.

---

## 5) System Quality & MLOps Readiness

### 5.1 Model Management
Artifacts are stored in `models/`. There is no consistent registry or metadata per model.  
Recommendation: adopt a `models/<domain>/<run_id>/` structure + metadata JSON.

### 5.2 Data Versioning
DVC config exists but data directories are still local.  
Recommendation: move dataset manifests + checksums into DVC and document retrieval.

### 5.3 Monitoring & Logging
Prometheus + Grafana configs exist under `deploy/`.  
Recommendation: add per‑model inference metrics (latency, confidence distribution drift).

### 5.4 CI / Tests
Multiple workflows exist. Tests appear to run in CI, but local training scripts are not validated in CI.  
Recommendation: add lightweight smoke tests for training pipelines (esp. voice).

---

## 6) Security & Ops

### 6.1 Secrets
.env is excluded from git, but local backups exist (`.env.save`, `.env.backup.*`).  
Recommendation: ensure all secrets are rotated and **never committed**.  

### 6.2 API Guardrails
Uploads are validated in `app/utils/uploads.py`.  
Recommendation: add rate limiting to audio endpoint in production, enforce maximum duration, and restrict CORS.

---

## 7) Key Risks & Gaps (Project‑wide)

**High**
- Voice emotion accuracy is low (≈54%); not production‑ready.
- Emotion dataset is acted and narrow; no real “crying” class.
- Training splits are random (not speaker‑independent) → leakage risk.

**Medium**
- Multiple overlapping training scripts (`scripts/train_production.py`, `scripts/retrain_all_98.py`, experimental scripts) → duplication + drift.
- Mixed UI stacks (Streamlit + React/Next + legacy) → deployment complexity.
- Stub endpoint exists in `src/api/audio.py` (unused) → confusion.

**Low**
- Large number of notebooks and reports in repo; hard to maintain.
- Logs and artifacts can bloat repo unless governed by LFS/ignore rules.

---

## 8) World‑Class Voice Emotion Detection Upgrade Plan

### 8.1 Target Definitions (must choose)
To reach “world‑class,” define a precise task:
- **Binary cry detection** (cry vs not‑cry) — most realistic path to >95% F1
- **3‑class** (cry / neutral / other‑emotion) — more practical than 5‑class
- **5‑class emotion** (angry/happy/neutral/sad/fearful) — harder to reach elite scores

For student/job portfolios: **binary or 3‑class** is the strongest, most defensible demo.

### 8.2 Data Expansion (required)
Current dataset is acted (CREMA‑D) and too small. Add real‑world datasets:
- **RAVDESS**, **TESS**, **IEMOCAP**, **Emo‑DB** for emotion diversity
- **VoxCeleb** (neutral speech, for negative examples)
- **Real crying audio** (public clips or curated set with consent)

Goal: **100k+ clips**, multi‑speaker, mixed noise, real emotion.

### 8.3 Model Upgrade (required)
Replace MFCC + RF with SSL audio encoders:
- Wav2Vec2 / HuBERT / WavLM encoder + classification head
- Optionally Whisper encoder embeddings for fusion
Benefits: superior generalization, robustness to noise, speaker variability.

### 8.4 Training Protocol
- **Speaker‑independent split** (train/val/test by speaker ID)
- Data augmentation: noise, reverb, speed/pitch shift, volume scaling
- Class balancing with weighted loss or oversampling
- Track **macro‑F1 / UAR / per‑class recall**, not just accuracy

### 8.5 Evaluation (world‑class proof)
- Cross‑dataset evaluation: train on CREMA‑D + RAVDESS, test on IEMOCAP (out‑of‑domain)
- Report: confusion matrix, per‑speaker performance, robustness under noise
- Calibrate confidence (temperature scaling)

### 8.6 Deployment Updates
- Export best model to ONNX/TorchScript for fast API inference
- Add `/api/voice/cry` endpoint if using binary classifier
- Add structured telemetry: latency, confidence drift, class distribution

---

## 9) Concrete Next Steps (I can implement)

**Phase 1: Data + Evaluation (1–2 days)**
1) Create speaker‑independent splits for voice dataset
2) Add audit notebook/report with duration, SR, and label stats
3) Add macro‑F1 + UAR metrics to training logs

**Phase 2: Model Upgrade (2–5 days)**
1) Add `wav2vec2`/`hubert` training script in `scripts/voice/`
2) Train baseline emotion model (5‑class)
3) Add optional cry‑detection head

**Phase 3: Deployment (1–2 days)**
1) Add endpoint, model registry entry, inference metrics
2) Update tests for new endpoint + metrics
3) Document model limits + accuracy expectation

---

## 10) Final Verdict

**Current state is not world‑class for emotion detection.**  
You have a solid multi‑domain project, but voice emotion needs a modern model + real‑world data to be competitive. The plan above is the fastest path to an elite, portfolio‑grade system.

If you want, I can immediately start Phase 1 (dataset audit + speaker split + proper metrics) and then Phase 2 (wav2vec2 training).
