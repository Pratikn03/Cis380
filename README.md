# Universal Anomaly Intelligence System (UAIS‑V)

UAIS‑V is a full-stack, multimodal anomaly intelligence project that ingests data across fraud, cyber, insider behavior, NLP emails/logs, and vision forgeries, then fuses the signals with explainability and deploys them to API + dashboard surfaces. The repo ships with lightweight experiment artifacts so the dashboard can be previewed without heavy training.

What’s inside:
- **Domain pipelines**: fraud, cyber, CERT behavior, NLP, vision, plus a generative VAE for tabular synthesis.
- **Model zoo**: supervised gradient boosting/logreg, unsupervised isolation forest/LOF/autoencoders, LSTM/TCN sequence models, DistilBERT text, ResNet18 vision.
- **Fusion + explainability**: stacked meta-model over domain scores, SHAP, saliency, Grad-CAM.
- **Orchestration + tracking**: Prefect flow stubs and MLflow logging hooks.
- **Deployment**: FastAPI endpoints and a Streamlit dashboard (with prefilled scores/plots under `experiments/` for instant demo).
- **Docs**: `docs/local_run.md` for quick API + dashboard startup.

## 📂 Repository Layout

```
├── config/                    # YAML configs per domain
├── data/                      # raw/interim/processed datasets
├── notebooks/                 # 00–100 experiment notebooks
├── src/uais/                  # core Python package
│   ├── data/                  # loaders
│   ├── features/              # feature builders
│   ├── supervised/            # fraud & cyber trainers
│   ├── anomaly/               # IF/LOF/autoencoder utilities
│   ├── sequence/              # LSTM/GRU helpers
│   ├── nlp/                   # text classifier baseline
│   ├── vision/                # image anomaly trainer
│   ├── generative/            # VAE synthesis pipeline
│   ├── fusion/                # meta-model + embeddings
│   ├── explainability/        # SHAP utilities
│   ├── drift/                 # drift analytics
│   └── orchestration/         # Prefect flow stubs
├── experiments/               # metrics, plots, saved scores
├── models/                    # persisted models per domain
├── dashboard/                 # Streamlit UI scaffolding
├── deploy/                    # FastAPI entrypoint (future use)
└── reports/                   # Word/PDF deliverables (to be generated)
```

## 🚀 Current Capabilities

- Fraud / Cyber / Behavior data ingestion + feature engineering; VAE synthesis for tabular fraud.
- Supervised fraud + cyber models (HistGB/LogReg) with light CV helpers.
- Unsupervised anomaly scores (IF/LOF/autoencoder/LSTM) and drift/explainability notebooks.
- Fusion meta-model + notebook to stack cross-domain scores.
- NLP (DistilBERT baseline) and vision (ResNet18) trainers with optional Kaggle downloads.
- Streamlit dashboard with pre-generated plots/scores for Fraud/Cyber/Behavior/Vision/Fusion.

## 🗺️ Roadmap Snapshot (now)

1. Leakage-free, fold-aware training (pipelines in flows; CV helpers available).
2. Modern baselines + ablations (boosting, feature engineering, fusion CV).
3. Explainability artifacts (SHAP, saliency, Grad-CAM) saved under `experiments/`.
4. Deployment surfaces (FastAPI + Streamlit; Docker Compose for API/MLflow/UI).
5. Reporting hooks (metrics summaries, plots) under `reports/` and `figures/`.

## 🧪 Quick Start

```bash
# 1) Environment
python -m venv .venv-macos
source .venv-macos/bin/activate  # Windows: .\.venv-macos\Scripts\activate
pip install -r requirements.txt

# 2) Data (Enron + CIFAR-10 helpers)
python scripts/download_data.py --all          # requires ~/.kaggle/kaggle.json
# or place data manually and re-run with --no-kaggle

# 3) Fast dashboard/API preview (ships with sample artifacts)
streamlit run dashboard/app_streamlit.py --server.port 8501
uvicorn deploy.api.main:app --reload --port 8000

# 4) Example: run fraud experiment end-to-end
PYTHONPATH=src python src/scripts/run_fraud_experiment.py
```

### Training Workflow (scripts/flows)

1. **Ingest + build features** (optional but recommended):
   ```bash
   bash scripts/run_ingest.sh
   bash scripts/run_build_features.sh
   ```
2. **Domain trainers** (run what you need; each calls the matching Prefect flow):
   ```bash
   bash scripts/run_train_fraud.sh      # LightGBM
   bash scripts/run_train_cyber.sh      # CatBoost
   bash scripts/run_train_behavior.sh   # LSTM/sequence
   bash scripts/run_train_nlp.sh        # DistilBERT
   bash scripts/run_train_vision.sh     # ResNet/ViT (detects nested Kaggle folders)
   python src/uais/generative/train_vae.py --config config/base_config.yaml  # optional VAE
   ```
3. **Fusion meta-model** (requires per-domain outputs in `experiments/`):
   ```bash
   bash scripts/run_fusion.sh
   ```
4. **One-shot pipeline** (ingest → features → all domains → fusion):
   ```bash
   bash scripts/run_full_fusion.sh
   ```

Artifacts land under `experiments/<domain>/…`, metrics under `reports/metrics_*.csv`, and MLflow runs under `src/mlruns/`, which the FastAPI + Streamlit layers read automatically.

Each notebook under `notebooks/` mirrors a script in `src/uais/...`. Swap in
your datasets by updating the matching config file under `config/`.

### 30-sequence module (UAIS-V, PyTorch TCN default)

Lightweight scaffolding for a 30-parallel-sequence classifier lives under
`src/uais_v`. Build synthetic/behavior-based sequences and train either the
fast PyTorch TCN model (default) or the TensorFlow version via:

```bash
python -m uais_v.cli.main build-30seq
python -m uais_v.cli.main train-30seq
```

Set `model.type` in `configs/model_30seq.yaml` to `multi_sequence_30_torch`
(default) or `multi_sequence_30_tf` to switch back to TensorFlow.

### Fusion meta-model (stacking)

Provide per-domain score files in `configs/fusion_baseline.yaml` and run:

```bash
bash scripts/run_fusion.sh
```

This trains a simple logistic regression stacker over domain scores and saves
the model to `experiments/fusion/models/fusion_meta_model.pkl`.

### NLP/Vision data download

- Run `python scripts/download_data.py --all` to fetch Enron emails (Kaggle API, requires `~/.kaggle/kaggle.json`) and CIFAR-10 (direct HTTP) into `data/raw/nlp` and `data/raw/vision`.
- Use `--no-kaggle` if you manually place `data/raw/nlp/enron_emails.csv`.

### NLP and Vision trainers

- NLP (DistilBERT): see `configs/nlp_baseline.yaml` and run `bash scripts/run_train_nlp.sh`
  (expects `data/processed/nlp/enron_emails.csv` with `text`/`label`; falls back to tiny sample).
- Vision (ResNet18): see `configs/vision_baseline.yaml` and run `bash scripts/run_train_vision.sh`
  (expects `data/processed/vision/train` and `val` folders).

### Serving (FastAPI) and Dashboard (Streamlit)

- FastAPI: `uvicorn deploy.api.main:app --reload --port 8000`  
  Endpoints: `/predict_fraud`, `/predict_cyber`, `/predict_fusion` (uses saved models if present).
- Streamlit: `streamlit run dashboard/app_streamlit.py`  
  Shows metrics/plots if placed under `experiments/<domain>/...`; sidebar lists available artifacts.
  Fraud/Cyber tabs will display SHAP summaries if generated by the Prefect flows; Behavior tab shows saliency CSV if present.

### Run everything (best-effort)
`bash scripts/run_full_fusion.sh` will run fraud, cyber, behavior, NLP, vision flows (with fallbacks) and then the fusion flow, producing scores and models for the API/Streamlit to consume.

## 🤝 Contributing / Next Steps

- Fork the repo or open an issue for missing modules.
- Add datasets to `data/raw/<domain>/` and update the configs.
- Run notebooks sequentially (00 → 100) or integrate the Prefect flows once
all datasets are staged.

UAIS‑V is maintained by **Pratik Niroula** as a showcase of full-stack anomaly
intelligence skills—from data engineering to AI deployment. Feel free to build
on top of it!  

### Docker Compose (API + Streamlit + MLflow)

From repo root:
```bash
docker-compose up --build
```
- API: http://localhost:8000
- Streamlit: http://localhost:8501
- MLflow: http://localhost:5000

Models/experiments are mounted from the repo; ensure artifacts (fraud/cyber/fusion, NLP/vision) exist for endpoints.
