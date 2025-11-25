# UAIS-V Technical Brief (Engineering Summary)

## Overview
Universal Anomaly Intelligence System (Vision-Enabled) is a multimodal AI stack for anomaly detection, explainability, and risk prediction across:
- Fraud (tabular)
- Cybersecurity (network intrusion)
- Behavioral / Insider Threat (CERT r4.2)
- Natural Language Processing (emails / text)
- Computer Vision (deepfake / forgery detection)

## Core Architecture
Layer | Purpose | Tools / Frameworks
--- | --- | ---
Data Layer | Ingestion, storage, cleaning | pandas, pyarrow, fastparquet
Feature Engineering | Domain-specific features/encodings | scikit-learn, category_encoders, numpy
Modeling | Supervised + unsupervised + sequence + multimodal fusion | XGBoost, LightGBM, CatBoost, PyTorch, TensorFlow (PyTorch Lightning as alt)
Explainability | Interpret predictions | SHAP, LIME, Grad-CAM (vision)
Orchestration | Automate pipelines | Prefect, MLflow
Deployment | Serve/visualize | FastAPI, Streamlit, Docker
Evaluation / Drift | Continuous validation | Evidently AI, custom drift scripts

## Data & File Flow
```
data/raw/ -> data/interim/ -> data/processed/
           -> src/uais/data/load_datasets.py
                fraud     -> build_fraud_feature_table()
                cyber     -> build_cyber_feature_table()
                behavior  -> build_behavior_sequences()
                nlp       -> preprocess_emails()
                vision    -> preprocess_images()
``` 
Outputs feed into supervised, unsupervised, sequence, NLP, vision trainers, and then the fusion meta-model.

## Modeling Stack by Domain
**Fraud (tabular)**
- Data: creditcard.csv
- Models: XGBoost, LightGBM, CatBoost, Logistic Regression baseline
- Metrics: ROC-AUC, F1, PR, latency
- Notes: tree ensembles preferred for speed/interpretability on structured data

**Cybersecurity**
- Data: UNSW-NB15
- Models: HistGradientBoosting, RandomForest, Autoencoder
- Frameworks: scikit-learn, LightGBM, Keras

**Behavior / Insider Threat (CERT r4.2)**
- Approach: sequence modeling with unsupervised LSTM autoencoders
- Data: logon.csv, device.csv, email.csv
- Current issue: slow TensorFlow CPU training
- Fixes: smaller batch/epochs, PyTorch Lightning or TCN, or run on GPU (Colab/AWS); reduce sequence length/users for quick tests

**NLP (text anomaly)**
- Data: Enron emails
- Pipeline: preprocess -> DistilBERT embeddings -> fine-tuned classifier (suspicious vs normal)
- Frameworks: transformers, torch, datasets

**Vision (deepfake/forgery)**
- Data: DFDC, CelebDF
- Models: ResNet18 baseline; optional GAN/VAE for synthesis
- Frameworks: torchvision, timm

## Fusion Meta-Model
Combine risk scores from fraud, cyber, behavior, NLP, vision -> stacking/blending (e.g., sklearn StackingClassifier) or weighted fusion -> unified risk index / recommendations. Artifacts stored under `experiments/fusion/`.

## Explainability & Drift
Layer | Tool | Output
--- | --- | ---
Tabular | SHAP | Feature contribution plots
Cyber/NLP | LIME | Text explanations
Vision | Grad-CAM | Image heatmaps
Drift | Evidently | Dataset/model drift reports

Outputs saved to `experiments/<domain>/plots/`.

## Orchestration & Deployment
- Prefect flows (ingest -> train -> eval -> log). Example: `python src/orchestration/fraud_flow.py`
- MLflow tracking for metrics/params/artifacts
- FastAPI + Docker for unified inference endpoint
- Streamlit dashboard for metrics, explainability, and risk index

## Performance Optimizations
Problem | Fix
--- | ---
TensorFlow slow on M-series | Use tensorflow-macos + tensorflow-metal, or switch to PyTorch
CPU-only training | Prefer HistGradientBoosting / LightGBM over deep nets
Slow CERT training | Limit rows/epochs, use TCN
Memory issues | Process Parquet in chunks
Slow explainability | Use approximate/fast SHAP mode

## End-to-End Flow (high level)
Raw data (fraud, cyber, behavior, NLP, vision)
 -> Ingestion -> Feature Engineering -> Model Training
 -> Per-domain models (supervised, unsupervised, sequence)
 -> Fusion meta-model (aggregate scores)
 -> Explainability + Drift analysis
 -> Orchestration (Prefect + MLflow)
 -> Deployment (FastAPI + Streamlit)

## Example Tech Stack
Type | Framework
--- | ---
Programming | Python 3.11
ML | scikit-learn 1.5, XGBoost 2.0, LightGBM 4.3
DL | TensorFlow 2.16 (or PyTorch 2.4 for speed)
NLP | Transformers 4.43
Vision | TorchVision 0.19
Orchestration | Prefect 3.x
Tracking | MLflow 2.15
Deployment | FastAPI 0.115, Docker 27
Visualization | Streamlit 1.38, Plotly 5.23

## Next Actions
1) Replace slow TensorFlow sequence model (add train_tcn.py with PyTorch TCN autoencoder).
2) Finish NLP & Vision modules (train_text_classifier.py, train_vision_model.py).
3) Integrate Prefect flows end-to-end.
4) Run fusion meta-model once domain scores are ready.
5) Deploy Streamlit dashboard for real-time risk visualization.
