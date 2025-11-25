"""FastAPI endpoint to serve UAIS-V predictions."""

from pathlib import Path
from typing import List

import joblib
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="UAIS-V API", version="1.0")

project_root = Path(__file__).resolve().parents[2]
fraud_model_path = project_root / "models" / "fraud" / "supervised" / "fraud_model.pkl"
cyber_model_path = project_root / "models" / "cyber" / "supervised" / "cyber_model.pkl"

fraud_model = joblib.load(fraud_model_path) if fraud_model_path.exists() else None
cyber_model = joblib.load(cyber_model_path) if cyber_model_path.exists() else None


class FraudRequest(BaseModel):
    features: List[float]


@app.get("/")
def root():
    return {"message": "UAIS-V API active. Use /predict_fraud to score."}


@app.post("/predict_fraud")
def predict_fraud(req: FraudRequest):
    if fraud_model is None:
        return {"error": "Fraud model not found."}
    X = np.array(req.features).reshape(1, -1)
    proba = fraud_model.predict_proba(X)[0, 1]
    return {"fraud_probability": float(proba)}
