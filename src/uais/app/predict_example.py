"""Local inference example for UAIS."""
import pandas as pd
import joblib

from uais.config.config_loader import load_config
from uais.utils.paths import domain_paths
from uais.utils.logging_utils import setup_logging

logger = setup_logging(__name__)


def load_artifact(domain: str):
    paths = domain_paths(domain)
    model_path = paths["models"] / f"{domain}_supervised.pkl"
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model artifact not found at {model_path}. Run the corresponding experiment script first."
        )
    return joblib.load(model_path)


def predict(domain: str, samples: list[dict]):
    model_bundle = load_artifact(domain)
    model = model_bundle if not isinstance(model_bundle, dict) else model_bundle.get("model", model_bundle)
    df = pd.DataFrame(samples)
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(df)[:, 1]
        return proba.tolist()
    return model.predict(df).tolist()


def demo():
    domain = "fraud"
    cfg = load_config(domain)
    example_samples = [
        {
            "amount": 123.4,
            "old_balance": 300.0,
            "new_balance": 176.6,
            "transaction_delta": -20.0,
            "tx_type": "TRANSFER",
            "channel": "web",
        }
    ]
    preds = predict(domain, example_samples)
    logger.info("Example predictions for %s: %s", domain, preds)


if __name__ == "__main__":
    demo()
