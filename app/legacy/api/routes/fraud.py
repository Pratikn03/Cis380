"""
==============================================================================
FRAUD DETECTION API ROUTE
==============================================================================
Author: Pratik Niroula
Project: Sentifargo (Sentifargo)

WHAT THIS FILE DOES:
--------------------
This file provides the API endpoint for fraud detection. It:
1. Loads a pre-trained fraud detection model (XGBoost, RandomForest, etc.)
2. Accepts transaction features as input
3. Returns a fraud probability score (0 = legitimate, 1 = fraudulent)

API ENDPOINT:
-------------
    POST /api/fraud
    
    Request Body:
        {"features": [0.5, -1.2, 3.4, ...]}  # List of numerical features
    
    Response:
        {
            "score": 0.87,              # Fraud probability (0-1)
            "input_features": 30,        # Number of features received
            "expected_features": 30,     # Number of features model expects
            "feature_names": [...]       # Names of features (if available)
        }

MODEL LOCATION:
---------------
    models/fraud/supervised/fraud_model.pkl

HOW FRAUD DETECTION WORKS:
--------------------------
    1. Extract features from transaction (amount, time, location, merchant type)
    2. Normalize features to same scale as training data
    3. Pass through trained model (XGBoost gradient boosting)
    4. Model outputs probability of fraud based on patterns learned
    
    Key fraud indicators the model looks for:
    - Unusual transaction amounts
    - Odd transaction times (e.g., 3 AM)
    - Geographic anomalies (card used far from usual location)
    - Velocity (many transactions in short time)
    - Merchant category patterns
==============================================================================
"""

from pathlib import Path

import joblib  # For loading saved sklearn/xgboost models (.pkl files)
import numpy as np  # For numerical array operations
import pandas as pd  # For creating DataFrames with feature names
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel  # For request validation

from ..deps import require_auth  # Authentication dependency

# ==============================================================================
# ROUTER SETUP
# ==============================================================================
# Create a router for fraud-related endpoints
# - prefix: All routes start with /api/fraud
# - tags: Groups endpoints in API documentation
# - dependencies: Requires authentication for all routes
router = APIRouter(prefix="/api/fraud", tags=["fraud"], dependencies=[Depends(require_auth)])


# ==============================================================================
# REQUEST MODEL
# ==============================================================================
class FraudRequest(BaseModel):
    """
    Request body schema for fraud prediction.

    The 'features' field should contain numerical values representing
    transaction characteristics. Common features include:
    - Transaction amount (normalized)
    - Time of day (encoded)
    - Days since last transaction
    - Transaction count in last hour
    - Distance from home location
    - etc.

    Example:
        {"features": [0.5, -1.2, 3.4, 0.0, 1.8, ...]}
    """

    features: list[float]  # List of numerical feature values


# ==============================================================================
# MODEL LOADING
# ==============================================================================
# Path to the trained fraud detection model
_model_path = Path("models") / "fraud" / "supervised" / "fraud_model.pkl"

# Cache variables - model is loaded once and reused
_fraud_model = None  # The loaded model object
_fraud_model_error: str | None = None  # Error message if loading failed


def _get_fraud_model():
    """
    Load and return the fraud detection model.

    This function implements lazy loading:
    - Model is only loaded when first needed
    - Once loaded, it's cached in memory for reuse
    - If loading fails, error is stored to avoid repeated attempts

    Returns:
        model: The loaded sklearn/xgboost model, or None if unavailable

    Why lazy loading?
    - Faster server startup (don't load all models immediately)
    - Memory efficient (models only loaded when needed)
    """
    global _fraud_model, _fraud_model_error

    # Return cached model if already loaded
    if _fraud_model is not None:
        return _fraud_model

    # Check if model file exists
    if not _model_path.exists():
        return None

    # Don't retry if previous load failed
    if _fraud_model_error is not None:
        return None

    # Attempt to load the model
    try:
        # joblib.load() reads the pickled model file
        _fraud_model = joblib.load(_model_path)
    except Exception as exc:  # pragma: no cover - depends on local env
        _fraud_model_error = str(exc)
        return None
    return _fraud_model


# ==============================================================================
# API ENDPOINT
# ==============================================================================
@router.post("")
def predict_fraud(req: FraudRequest):
    """
    Predict fraud probability for a transaction.
    
    This endpoint:
    1. Loads the fraud model (if not already loaded)
    2. Prepares input features in the correct format
    3. Runs model inference
    4. Returns fraud probability score
    
    Args:
        req: FraudRequest containing list of feature values
        
    Returns:
        dict: {
            "score": float,           # Fraud probability 0.0 to 1.0
            "input_features": int,    # Number of features provided
            "expected_features": int, # Number model expects
            "feature_names": list     # Names of features (if known)
        }
        
    Raises:
        HTTPException 503: If model is not available
        HTTPException 500: If inference fails
        
    Example usage with curl:
        curl -X POST http://localhost:8000/api/fraud \\
             -H "Content-Type: application/json" \\
             -d '{"features": [0.5, -1.2, 3.4, 0.0, 1.8]}'
    """
    # Load the fraud model
    fraud_model = _get_fraud_model()

    # Return error if model not available
    if fraud_model is None:
        detail = "Fraud model not found."
        if _model_path.exists() and _fraud_model_error:
            detail = f"Fraud model failed to load: {_fraud_model_error}"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        )

    try:
        # ==============================================================
        # PREPARE INPUT DATA
        # ==============================================================
        # Get feature names from model (if it has them)
        cols = list(getattr(fraud_model, "feature_names_in_", []))

        if cols:
            # Model has named features - create DataFrame with correct columns
            # Initialize all values to 0.0
            values = [0.0] * len(cols)
            # Fill in provided values (up to number of columns)
            for i, v in enumerate(req.features[: len(cols)]):
                values[i] = float(v)
            # Create pandas DataFrame with feature names
            X = pd.DataFrame([values], columns=cols)
        else:
            # Model doesn't have named features - use raw numpy array
            X = np.array(req.features, dtype=float).reshape(1, -1)

        # ==============================================================
        # RUN PREDICTION
        # ==============================================================
        if hasattr(fraud_model, "predict_proba"):
            # Classification model - get probability of fraud (class 1)
            # predict_proba returns [[prob_class_0, prob_class_1]]
            score = float(fraud_model.predict_proba(X)[0][1])
        elif hasattr(fraud_model, "decision_function"):
            # SVM or similar - get decision function score
            score = float(fraud_model.decision_function(X)[0])
        else:
            # Regression model or simple classifier - get raw prediction
            score = float(fraud_model.predict(X)[0])

        # ==============================================================
        # RETURN RESULTS
        # ==============================================================
        return {
            "score": score,  # Fraud probability
            "input_features": len(req.features),  # Features received
            "expected_features": len(cols) if cols else None,  # Features expected
            "feature_names": cols or None,  # Feature names
        }

    except Exception as exc:
        # Handle any errors during inference
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fraud inference failed: {exc}",
        )
