"""
Supervised fraud modeling with multiple model options.
"""
from dataclasses import dataclass
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold

from uais.utils.metrics import compute_classification_metrics


@dataclass
class FraudModelConfig:
    """Configuration for the fraud supervised model."""

    model_type: str = "hist_gb"  # hist_gb | logreg | xgboost | lightgbm | catboost
    random_state: int = 42
    max_depth: int = 4
    learning_rate: float = 0.1
    max_iter: int = 200  # for hist_gb or logistic regression
    n_estimators: int = 300  # used by xgboost/lightgbm/catboost


def _build_model(config: FraudModelConfig):
    """Construct a model instance based on config.model_type."""

    mtype = config.model_type.lower()
    if mtype == "logreg":
        return LogisticRegression(
            max_iter=config.max_iter,
            class_weight="balanced",
        )
    if mtype == "hist_gb":
        return HistGradientBoostingClassifier(
            max_depth=config.max_depth,
            learning_rate=config.learning_rate,
            max_iter=config.max_iter,
            random_state=config.random_state,
        )
    if mtype == "xgboost":
        try:
            from xgboost import XGBClassifier
        except ImportError as exc:  # pragma: no cover
            raise ImportError("Install xgboost to use model_type='xgboost'") from exc
        return XGBClassifier(
            n_estimators=config.n_estimators,
            learning_rate=config.learning_rate,
            max_depth=config.max_depth,
            subsample=0.9,
            colsample_bytree=0.9,
            objective="binary:logistic",
            eval_metric="logloss",
            random_state=config.random_state,
            n_jobs=-1,
        )
    if mtype == "lightgbm":
        try:
            from lightgbm import LGBMClassifier
        except ImportError as exc:  # pragma: no cover
            raise ImportError("Install lightgbm to use model_type='lightgbm'") from exc
        return LGBMClassifier(
            n_estimators=config.n_estimators,
            learning_rate=config.learning_rate,
            max_depth=config.max_depth,
            objective="binary",
            random_state=config.random_state,
        )
    if mtype == "catboost":
        try:
            from catboost import CatBoostClassifier
        except ImportError as exc:  # pragma: no cover
            raise ImportError("Install catboost to use model_type='catboost'") from exc
        return CatBoostClassifier(
            iterations=config.n_estimators,
            learning_rate=config.learning_rate,
            depth=config.max_depth,
            random_seed=config.random_state,
            verbose=False,
            loss_function="Logloss",
        )
    raise ValueError(f"Unknown model_type: {config.model_type}")


def train_fraud_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    config: FraudModelConfig,
) -> Tuple[Any, Dict[str, float]]:
    """Train a supervised fraud model and return model + validation metrics."""
    model = _build_model(config)
    model.fit(X_train, y_train)

    # Predict probabilities for positive class (fraud).
    if hasattr(model, "predict_proba"):
        y_val_prob = model.predict_proba(X_val)[:, 1]
    else:
        scores = model.decision_function(X_val)
        y_val_prob = 1.0 / (1.0 + np.exp(-scores))

    metrics_dict = compute_classification_metrics(y_val.values, y_val_prob, threshold=0.5)
    return model, metrics_dict


def cross_val_train_fraud(
    X: pd.DataFrame,
    y: pd.Series,
    config: FraudModelConfig,
    n_splits: int = 3,
    random_state: int = 42,
) -> Tuple[list[Any], Dict[str, float]]:
    """Stratified K-fold training for stability; uses low n_splits to limit budget."""
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    aucs = []
    models = []
    for train_idx, val_idx in skf.split(X, y):
        X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_tr, y_val = y.iloc[train_idx], y.iloc[val_idx]
        model = _build_model(config)
        model.fit(X_tr, y_tr)
        proba = model.predict_proba(X_val)[:, 1] if hasattr(model, "predict_proba") else model.predict(X_val)
        aucs.append(compute_classification_metrics(y_val.values, proba, threshold=0.5)["roc_auc"])
        models.append(model)
    metrics = {"cv_roc_auc_mean": float(np.mean(aucs)) if aucs else float("nan")}
    return models, metrics
