# UAIS-V API and Dashboard Notes

## FastAPI (deploy/api/main.py)
- Endpoints: `/`, `/predict_fraud`, `/predict_cyber`, `/predict_fusion`, `/predict_nlp`, `/predict_vision`
- Models loaded if present:
  - Fraud: `models/fraud/supervised/fraud_model.pkl`
  - Cyber: `models/cyber/supervised/cyber_model.pkl`
  - Fusion: `experiments/fusion/models/fusion_meta_model.pkl`
  - NLP: `models/nlp/distilbert/` (tokenizer + model.pt)
  - Vision: `models/vision/resnet/model.pt`
- Fusion expects a dict of domain scores; keys are sorted before prediction.

Run locally:
```bash
uvicorn deploy.api.main:app --reload --port 8000
```
NLP expects DistilBERT artifacts saved under `models/nlp/distilbert/`; Vision expects a `model.pt` under `models/vision/resnet/`.
## Streamlit (dashboard/app_streamlit.py)
- Shows metrics for Fraud/Cyber if CSVs exist under `experiments/<domain>/metrics/metrics.csv`
- Behavior tab displays plot from `experiments/behavior/plots/heatmap.png` if present.
- Fusion tab shows `experiments/fusion/fusion_scores.csv` (scatter if columns available).
- Sidebar lists which model artifacts exist.

Run locally:
```bash
streamlit run dashboard/app_streamlit.py
```
