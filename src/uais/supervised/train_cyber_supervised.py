from dataclasses import dataclass
from typing import Literal, Tuple, Dict

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

from uais.utils.metrics import compute_classification_metrics

ModelType = Literal["hist_gb", "logreg", "xgboost", "lightgbm", "catboost"]


@dataclass
class CyberModelConfig:
    model_type: ModelType = "hist_gb"
    max_depth: int = 6
    learning_rate: float = 0.1
    max_iter: int = 200
    n_estimators: int = 300
    random_state: int = 42


def _build_model(config: CyberModelConfig):
    mtype = config.model_type.lower()
    if mtype == "hist_gb":
        return HistGradientBoostingClassifier(
            max_depth=config.max_depth,
            learning_rate=config.learning_rate,
            max_iter=config.max_iter,
            random_state=config.random_state,
        )
    if mtype == "logreg":
        return LogisticRegression(
            max_iter=config.max_iter,
            n_jobs=-1,
            class_weight="balanced",
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


def train_cyber_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    config: CyberModelConfig,
) -> Tuple[object, Dict[str, float]]:
    """Train a supervised cyber intrusion model and return model + validation metrics."""
    model = _build_model(config)
    model.fit(X_train, y_train)

    if hasattr(model, "predict_proba"):
        y_val_prob = model.predict_proba(X_val)[:, 1]
    else:
        scores = model.decision_function(X_val)
        y_val_prob = 1.0 / (1.0 + np.exp(-scores))

    val_metrics = compute_classification_metrics(y_val.values, y_val_prob, threshold=0.5)
    return model, val_metrics
