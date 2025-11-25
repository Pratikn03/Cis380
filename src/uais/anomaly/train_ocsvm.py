"""One-Class SVM training for anomaly scoring."""
from typing import Dict, Tuple

import joblib
import numpy as np
from sklearn.svm import OneClassSVM

from uais.utils.logging_utils import setup_logging
from uais.utils.paths import domain_paths

logger = setup_logging(__name__)


def train_ocsvm(df, target: str, preprocessor, config: Dict, domain: str) -> Tuple[OneClassSVM, np.ndarray]:
    """
    Fit a One-Class SVM on preprocessed features and return scores.
    Scores are negated decision function values so higher = more anomalous.
    """
    contamination = config.get("training", {}).get("anomaly_contamination", 0.05)
    X = df.drop(columns=[target])
    y = df[target]

    X_processed = preprocessor.fit_transform(X)
    if hasattr(X_processed, "toarray"):
        X_processed = X_processed.toarray()

    ocsvm = OneClassSVM(nu=contamination, kernel="rbf", gamma="scale")
    ocsvm.fit(X_processed)
    scores = -ocsvm.decision_function(X_processed).ravel()

    paths = domain_paths(domain)
    paths["models"].mkdir(parents=True, exist_ok=True)
    artifact = paths["models"] / f"{domain}_ocsvm.pkl"
    joblib.dump({"model": ocsvm, "preprocessor": preprocessor}, artifact)
    logger.info("Saved One-Class SVM for %s to %s", domain, artifact)

    return ocsvm, scores, y


__all__ = ["train_ocsvm"]
