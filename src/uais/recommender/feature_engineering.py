"""Meta-feature builder for the recommender."""
from __future__ import annotations

from typing import Dict, List, Tuple, Any

import numpy as np

from .utils import safe_float


META_FEATURE_NAMES: List[str] = [
    "fraud_score",
    "cyber_score",
    "behavior_score",
    "fusion_score",
    "max_domain_score",
    "min_domain_score",
    "domain_risk_spread",
    "fraud_is_max",
    "cyber_is_max",
    "behavior_is_max",
    "log_amount",
    "is_high_amount",
]


def build_meta_features(scores: Dict[str, float], event_features: Dict[str, Any]) -> Tuple[np.ndarray, List[str]]:
    """Build a numeric meta-feature vector for the recommender model."""
    fraud = float(scores.get("fraud", 0.0))
    cyber = float(scores.get("cyber", 0.0))
    behavior = float(scores.get("behavior", 0.0))
    fusion = float(scores.get("fusion", 0.0))

    domain_scores = np.array([fraud, cyber, behavior], dtype=float)
    max_dom = float(np.max(domain_scores))
    min_dom = float(np.min(domain_scores))
    spread = max_dom - min_dom

    fraud_is_max = 1.0 if fraud == max_dom and max_dom > 0 else 0.0
    cyber_is_max = 1.0 if cyber == max_dom and max_dom > 0 else 0.0
    behavior_is_max = 1.0 if behavior == max_dom and max_dom > 0 else 0.0

    raw_amount_keys = ["amount", "Amount", "transaction_amount", "amt"]
    amount_val = 0.0
    for k in raw_amount_keys:
        if k in event_features:
            amount_val = safe_float(event_features.get(k, 0.0), 0.0)
            break

    if amount_val > 0:
        import math

        log_amount = math.log1p(amount_val)
        is_high_amount = 1.0 if amount_val > 1000 else 0.0
    else:
        log_amount = 0.0
        is_high_amount = 0.0

    meta = np.array(
        [
            fraud,
            cyber,
            behavior,
            fusion,
            max_dom,
            min_dom,
            spread,
            fraud_is_max,
            cyber_is_max,
            behavior_is_max,
            log_amount,
            is_high_amount,
        ],
        dtype=float,
    )

    return meta, META_FEATURE_NAMES


__all__ = ["build_meta_features", "META_FEATURE_NAMES"]
