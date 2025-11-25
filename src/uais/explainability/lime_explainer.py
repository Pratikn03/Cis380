"""LIME helper functions."""
from typing import Dict, List

import numpy as np
import pandas as pd

from uais.utils.logging_utils import setup_logging

logger = setup_logging(__name__)


def explain_with_lime(model, X_train: pd.DataFrame, sample: pd.Series, class_names: List[str] | None = None) -> Dict:
    try:
        from lime.lime_tabular import LimeTabularExplainer
    except ImportError as exc:  # pragma: no cover - optional dependency path
        raise ImportError("Install `lime` to run LIME explanations") from exc

    explainer = LimeTabularExplainer(
        training_data=np.array(X_train),
        feature_names=X_train.columns,
        class_names=class_names or ["normal", "anomaly"],
        mode="classification",
    )
    exp = explainer.explain_instance(sample.values, model.predict_proba)
    explanation = dict(exp.as_list())
    logger.info("Computed LIME explanation for sample")
    return explanation


__all__ = ["explain_with_lime"]
