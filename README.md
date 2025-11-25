# Universal Anomaly Intelligence System (UAIS‑V)

UAIS‑V (Universal Anomaly Intelligence System with Multimodal Fusion) is an
end‑to‑end anomaly intelligence framework that spans fraud analytics,
cybersecurity intrusion detection, insider behavior monitoring, NLP log
analysis, document forgery detection, generative data synthesis, and
cross‑domain fusion.

The repository contains:

- **Multi-domain data pipelines** (fraud, cyber, CERT behavior, NLP, vision).
- **Supervised + unsupervised models** (gradient boosting, isolation forest,
autoencoders, LSTM sequence models).
- **Fusion + explainability** layers (stacked anomaly score, SHAP, drift).
- **Experiment tracking + orchestration** stubs (MLflow, Prefect flows).
- **Deployment surfaces** (FastAPI + Streamlit dashboard skeleton).

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

- Fraud / Cyber / Behavior (CERT) data ingestion + feature engineering.
- Supervised fraud + cyber models (HistGB, Logistic Regression).
- Unsupervised anomaly scores (Isolation Forest, LOF, autoencoder, LSTM).
- Fusion notebook + scripts for stacking cross-domain scores.
- Explainability + drift notebooks with shared plotting utilities.
- Placeholders for NLP, vision, generative, and dashboard orchestration to be
enabled once data is provided.

## 🗺️ Roadmap Snapshot

1. Finish populating new datasets (emails, forged documents, etc.).
2. Wire notebooks 70/80/90/100 to their respective modules.
3. Enable MLflow tracking + Prefect deployments per domain.
4. Flesh out FastAPI + Streamlit deployment story.
5. Export docx/pdf reports summarising experiments.

## 🧪 Quick Start

```bash
python -m venv .venv
source .venv/bin/activate  # on Windows use .venv\Scripts\activate
pip install -r requirements.txt

# Example: run fraud experiment end‑to‑end
python src/scripts/run_fraud_experiment.py
```

Each notebook under `notebooks/` mirrors a script in `src/uais/...`. You can
swap in your own datasets by updating the matching config file under
`config/`.

## 🤝 Contributing / Next Steps

- Fork the repo or open an issue for missing modules.
- Add datasets to `data/raw/<domain>/` and update the configs.
- Run notebooks sequentially (00 → 100) or integrate the Prefect flows once
all datasets are staged.

UAIS‑V is maintained by **Pratik Niroula** as a showcase of full-stack anomaly
intelligence skills—from data engineering to AI deployment. Feel free to build
on top of it!  
