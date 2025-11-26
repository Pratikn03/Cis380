"""Explain recommendations with rule-based text and optional SHAP."""
from __future__ import annotations

from typing import Dict, Any, List, Optional

import numpy as np

try:
    import shap  # type: ignore

    _SHAP_AVAILABLE = True
except Exception:
    _SHAP_AVAILABLE = False


def _build_rule_based_explanation(action: str, scores: Dict[str, float]) -> str:
    fraud = scores.get("fraud", 0.0)
    cyber = scores.get("cyber", 0.0)
    behavior = scores.get("behavior", 0.0)
    fusion = scores.get("fusion", 0.0)

    lines = [f"The fused anomaly risk is {fusion:.3f}."]
    if fraud > 0.7:
        lines.append("Fraud model flags this event as high risk.")
    elif fraud > 0.4:
        lines.append("Fraud model sees moderate risk.")
    else:
        lines.append("Fraud model sees low risk.")

    if cyber > 0.7:
        lines.append("Cyber model flags strong anomalies.")
    elif cyber > 0.4:
        lines.append("Cyber model sees some suspicious patterns.")
    else:
        lines.append("Cyber model sees low risk.")

    if behavior > 0.7:
        lines.append("Behavior model shows significant deviation.")
    elif behavior > 0.4:
        lines.append("Behavior model shows mild deviation.")
    else:
        lines.append("Behavior appears normal.")

    lines.append(f"Recommended action: **{action}**.")
    return " ".join(lines)


def _shap_top_features_text(
    rec_model: Any,
    meta_features: np.ndarray,
    meta_feature_names: List[str],
    action: str,
    max_features: int = 5,
) -> Optional[str]:
    """Compute SHAP values for the recommender model and describe top features."""
    if not _SHAP_AVAILABLE or rec_model is None:
        return None

    try:
        explainer = shap.TreeExplainer(rec_model)
        shap_vals = explainer.shap_values(meta_features)
        if isinstance(shap_vals, list):
            class_names = getattr(rec_model, "classes_", None)
            if class_names is not None:
                try:
                    cls_idx = list(class_names).index(action)
                except ValueError:
                    cls_idx = 0
            else:
                cls_idx = 0
            sv = shap_vals[cls_idx][0]
        else:
            sv = shap_vals[0]

        sv = np.array(sv)
        abs_sv = np.abs(sv)
        idx_sorted = np.argsort(-abs_sv)[:max_features]

        lines = ["Key factors influencing this decision:"]
        for idx in idx_sorted:
            fname = meta_feature_names[idx]
            contrib = sv[idx]
            direction = "increased" if contrib > 0 else "decreased"
            lines.append(f"- {fname} ({direction} risk, SHAP={contrib:+.3f})")
        return " ".join(lines)
    except Exception as exc:
        print(f"[explain] SHAP explanation failed: {exc}")
        return None


def explain_recommendation(
    action: str,
    scores: Dict[str, float],
    event_features: Dict[str, Any],
    rec_model: Any = None,
    meta_features: Optional[np.ndarray] = None,
    meta_feature_names: Optional[List[str]] = None,
) -> str:
    """Combine rule-based and optional SHAP explanation."""
    base_text = _build_rule_based_explanation(action, scores)
    shap_text = None
    if (
        rec_model is not None
        and meta_features is not None
        and meta_feature_names is not None
        and meta_features.shape[0] >= 1
    ):
        shap_text = _shap_top_features_text(
            rec_model=rec_model,
            meta_features=meta_features,
            meta_feature_names=meta_feature_names,
            action=action,
        )

    if shap_text:
        return base_text + " " + shap_text
    return base_text


__all__ = ["explain_recommendation"]
