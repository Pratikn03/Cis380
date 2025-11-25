"""Simple feedforward autoencoder for anomaly scoring."""
from typing import Dict, Tuple

import joblib
import numpy as np
from sklearn.neural_network import MLPRegressor

from uais.utils.logging_utils import setup_logging
from uais.utils.paths import domain_paths

logger = setup_logging(__name__)


def train_autoencoder(df, target: str, preprocessor, config: Dict, domain: str) -> Tuple[MLPRegressor, np.ndarray]:
    X = df.drop(columns=[target])
    y = df[target]
    X_processed = preprocessor.fit_transform(X)
    if hasattr(X_processed, "toarray"):
        X_processed = X_processed.toarray()

    model = MLPRegressor(
        hidden_layer_sizes=(64, 32, 64),
        max_iter=200,
        learning_rate_init=0.001,
        random_state=config.get("seed", 42),
    )
    model.fit(X_processed, X_processed)
    recon = model.predict(X_processed)
    errors = np.mean((X_processed - recon) ** 2, axis=1)

    paths = domain_paths(domain)
    paths["models"].mkdir(parents=True, exist_ok=True)
    artifact = paths["models"] / f"{domain}_autoencoder.pkl"
    joblib.dump({"model": model, "preprocessor": preprocessor}, artifact)
    logger.info("Saved autoencoder for %s to %s", domain, artifact)

    return model, errors, y


__all__ = ["train_autoencoder"]
