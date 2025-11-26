"""Fusion model that learns from multiple domain embeddings/scores."""
from typing import Dict, Tuple

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.preprocessing import StandardScaler

from uais.fusion.build_embeddings import generate_meta_features
from uais.utils.logging_utils import setup_logging
from uais.utils.metrics import classification_metrics
from uais.utils.paths import domain_paths, ensure_directories

logger = setup_logging(__name__)


def train_fusion_meta_model(
    score_dict: Dict[str, np.ndarray],
    labels: np.ndarray,
    config: Dict,
) -> Tuple[LogisticRegression, Dict[str, float]]:
    ensure_directories()
    X_meta = generate_meta_features(score_dict)
    y = np.asarray(labels)[: X_meta.shape[0]]

    scaler = StandardScaler()
    X_meta = scaler.fit_transform(X_meta)

    X_train, X_test, y_train, y_test = train_test_split(
        X_meta, y, test_size=config.get("data", {}).get("test_size", 0.2), random_state=config.get("seed", 42), stratify=y
    )

    model = LogisticRegression(max_iter=200, class_weight="balanced")
    model.fit(X_train, y_train)

    y_test_proba = model.predict_proba(X_test)[:, 1]
    metrics = classification_metrics(y_test, y_test_proba, threshold=0.5)

    # Cross-validated ROC-AUC for stability
    cv_scores = []
    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=config.get("seed", 42))
    for train_idx, val_idx in skf.split(X_meta, y):
        X_tr, X_val = X_meta[train_idx], X_meta[val_idx]
        y_tr, y_val = y[train_idx], y[val_idx]
        cv_model = LogisticRegression(max_iter=200, class_weight="balanced")
        cv_model.fit(X_tr, y_tr)
        proba = cv_model.predict_proba(X_val)[:, 1]
        fold_metrics = classification_metrics(y_val, proba, threshold=0.5)
        cv_scores.append(fold_metrics.get("roc_auc", float("nan")))
    metrics["cv_roc_auc_mean"] = float(np.nanmean(cv_scores)) if cv_scores else float("nan")

    paths = domain_paths("fusion")
    paths["models"].mkdir(parents=True, exist_ok=True)
    artifact = paths["models"] / "fusion_meta_model.pkl"
    joblib.dump({"model": model, "scaler": scaler}, artifact)
    logger.info("Saved fusion meta-model to %s", artifact)

    return model, metrics


__all__ = ["train_fusion_meta_model"]
