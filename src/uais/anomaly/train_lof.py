"""Local Outlier Factor training."""
from typing import Dict, Tuple

import joblib
import numpy as np
from sklearn.neighbors import LocalOutlierFactor

from uais.utils.logging_utils import setup_logging
from uais.utils.paths import domain_paths

logger = setup_logging(__name__)


def train_lof(df, target: str, preprocessor, config: Dict, domain: str) -> Tuple[LocalOutlierFactor, np.ndarray]:
    contamination = config.get("training", {}).get("anomaly_contamination", 0.05)
    X = df.drop(columns=[target])
    y = df[target]

    X_processed = preprocessor.fit_transform(X)
    if hasattr(X_processed, "toarray"):
        X_processed = X_processed.toarray()
    lof = LocalOutlierFactor(
        contamination=contamination,
        novelty=True,
    )
    lof.fit(X_processed)
    scores = -lof.score_samples(X_processed)

    paths = domain_paths(domain)
    paths["models"].mkdir(parents=True, exist_ok=True)
    artifact = paths["models"] / f"{domain}_lof.pkl"
    joblib.dump({"model": lof, "preprocessor": preprocessor}, artifact)
    logger.info("Saved LOF for %s to %s", domain, artifact)

    return lof, scores, y


__all__ = ["train_lof"]
