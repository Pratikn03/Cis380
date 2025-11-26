# Local Run Guide (API + Dashboard)

## Prerequisites
- Python 3.11
- Install dependencies: `pip install -r requirements.txt`
- Data in place (fraud/cyber/behavior, NLP/Vision as needed)
- Models/artifacts generated (run flows or scripts to create `models/...` and `experiments/...`)

## Start FastAPI
```
uvicorn deploy.api.main:app --reload --host 0.0.0.0 --port 8000
```
- Health: http://localhost:8000/health
- Root availability: http://localhost:8000/
- Endpoints: `/predict_fraud`, `/predict_cyber`, `/predict_fusion`, `/predict_nlp`, `/predict_vision`

## Start Streamlit
```
streamlit run dashboard/app_streamlit.py --server.address 0.0.0.0 --server.port 8501
```
- Dashboard: http://localhost:8501

## Docker Compose (API + Streamlit + MLflow)
From repo root:
```
docker-compose up --build
```
- API: http://localhost:8000
- Streamlit: http://localhost:8501
- MLflow: http://localhost:5000

## Generate artifacts quickly (best effort)
```
bash scripts/run_full_fusion.sh
```
This runs the flows and produces scores/plots/models for the dashboard/API to consume.
