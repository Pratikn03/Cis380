"""Fusion model that learns from multiple domain embeddings/scores."""
from typing import Dict, Tuple

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

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

    X_train, X_test, y_train, y_test = train_test_split(
        X_meta, y, test_size=config.get("data", {}).get("test_size", 0.2), random_state=config.get("seed", 42), stratify=y
    )

    model = LogisticRegression(max_iter=200, class_weight="balanced")
    model.fit(X_train, y_train)

    y_test_proba = model.predict_proba(X_test)[:, 1]
    metrics = classification_metrics(y_test, model.predict(X_test), y_test_proba)

    paths = domain_paths("fusion")
    paths["models"].mkdir(parents=True, exist_ok=True)
    artifact = paths["models"] / "fusion_meta_model.pkl"
    joblib.dump(model, artifact)
    logger.info("Saved fusion meta-model to %s", artifact)

    return model, metrics


__all__ = ["train_fusion_meta_model"]
