# Experimental Assets

This repo contains a number of research notebooks, ad-hoc scripts, and auxiliary folders that document discovery work and proof-of-concept experiments. They are not required for the core API/agent deployment but are kept for transparency. The sections below describe what lives there and how to treat it.

## Notebooks

| Notebook | Purpose |
| --- | --- |
| `00_data_overview.ipynb` | Global data quality checks and schema notes for all datasets. |
| `01_eda_fraud.ipynb` / `02_eda_cyber.ipynb` / `03_eda_behavior*.ipynb` | Exploratory data analysis for each anomaly domain (credit card fraud, UNSW-NB15, CERT behavior). |
| `10_supervised_fraud.ipynb`, `11_supervised_cyber.ipynb` | Supervised model prototyping for the fraud and cyber domains. |
| `20_unsupervised_fraud.ipynb`, `21_unsupervised_cyber.ipynb`, `22_unsupervised_behavior.ipynb` | Unsupervised/anomaly detection experiments for tabular data. |
| `30_sequence_models.ipynb` | Sequence-feature experiments (30-seq pipeline) used by downstream tests. |
| `40_*` series (fusion/hybrid fraud) | Fusion model analyses and hybrid scoring benchmarks. |
| `50_explainability.ipynb` | Visualizes SHAP/LIME/GradCAM explainability outputs. |
| `60_evaluation_drift.ipynb` | Drift detection experiments (vision, text). |
| `70_nlp_email_anomalies.ipynb` | NLP-driven anomaly detection on email text. |
| `80_vision_forgery_detection.ipynb` | Vision forgery detection/autoencoder prototypes. |
| `90_generative_synthesis.ipynb`, `95_data_quickstart.ipynb` | Generative/rapid data prep ideas. |
| `96_reports_preview.ipynb`, `97_feature_ablation.ipynb`, `98_task_checklist.ipynb`, `99_integration_overview.ipynb`, `100_fusion_and_dashboard.ipynb` | Reporting, ablation, and integration summaries. |

Keep these notebooks for reference or move them into an `archive/` folder if they are no longer maintained.

## Script Utilities

Scripts under `scripts/` automate dataset downloads and training prototypes. Key helpers are:

- `download_movielens.py`, `download_data.py`, `run_ingest.sh` – fetch raw data archives and build processed files.  
- `run_train_*` scripts – wrappers for the fraud/cyber/NLP/vision/sequence training pipelines (they call into `src/uais*` helpers).  
- `run_fusion.sh`, `run_full_fusion.sh`, `run_build_features.sh`, `run_build_30seq.sh` – orchestrate feature-building, 30-sequence generation, and fusion model training.  
- `start_all.sh` – convenience script to launch backend + Streamlit UI (already referenced in the README).  
- `api_latency_check.py`, `ci_smoke.py`, `build_items_from_archive.py` – miscellaneous tooling for manual checks and dataset preparation (keep them in `scripts/` as reference or move into an `experiments/` subfolder if unused).

## Miscellaneous Folders

- `experiments/` and `figures/` contain side-project outputs (plots, logs, etc.). Archive or remove stale files as you prepare the repo for release.  
- `rag/vector_store/` and `rag/service.py` continue to evolve; keep them aligned with the README if you replace TF-IDF with a proper vector DB.

## Recommendation

Mark folders as “experimental” in documentation (as above) and avoid importing them from production code. When the repository is ready for publication, you can optionally:

1. Move obsolete notebooks/scripts into `archive/` or `docs/archive.md` with a short summary.  
2. Keep this file updated so future contributors know which assets are “research-only.”
