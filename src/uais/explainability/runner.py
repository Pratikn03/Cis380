"""Central explainability runner for UAIS.

Provides helpers to generate SHAP/LIME for tabular models, text LIME/SHAP (optional),
and vision Grad-CAM is handled in vision flows.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

import numpy as np
import pandas as pd


def shap_tabular(model, X: pd.DataFrame, out_dir: Path, class_index: int = 1) -> Optional[Path]:
    try:
        import shap
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover
        print(f"SHAP skipped: {exc}")
        return None

    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)
        plt.figure()
        shap.summary_plot(shap_values[class_index] if isinstance(shap_values, list) else shap_values, X, show=False)
        plt.tight_layout()
        out_path = out_dir / "shap_summary.png"
        plt.savefig(out_path, dpi=150)
        plt.close()
        return out_path
    except Exception as exc:  # pragma: no cover
        print(f"SHAP generation failed: {exc}")
        return None


def lime_tabular(model, X_train: pd.DataFrame, sample: pd.Series, out_dir: Path, class_names=None) -> Optional[Path]:
    try:
        from lime.lime_tabular import LimeTabularExplainer
    except Exception as exc:  # pragma: no cover
        print(f"LIME skipped: {exc}")
        return None

    explainer = LimeTabularExplainer(
        training_data=np.array(X_train),
        feature_names=X_train.columns,
        class_names=class_names or ["normal", "anomaly"],
        mode="classification",
    )
    exp = explainer.explain_instance(sample.values, model.predict_proba)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "lime_explanation.txt"
    out_path.write_text(str(exp.as_list()))
    return out_path


def lime_text(model, text: str, out_dir: Path) -> Optional[Path]:
    try:
        from lime.lime_text import LimeTextExplainer
    except Exception as exc:  # pragma: no cover
        print(f"LIME text skipped: {exc}")
        return None

    explainer = LimeTextExplainer(class_names=["normal", "anomaly"])
    try:
        predict_fn = model.predict_proba if hasattr(model, "predict_proba") else None
        if predict_fn is None:
            raise AttributeError("Model does not implement predict_proba")
        exp = explainer.explain_instance(text, lambda x: predict_fn(x))
    except Exception as exc:
        print(f"LIME text generation failed: {exc}")
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "lime_text.txt"
    out_path.write_text(str(exp.as_list()))
    return out_path


def export_tabular_explainability(
    model,
    X_train: pd.DataFrame,
    X_val: pd.DataFrame,
    out_dir: Path,
    class_names=None,
) -> dict:
    """Generate SHAP + LIME artifacts best-effort; returns dict of file paths."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts = {"shap": None, "lime": None}

    shap_path = shap_tabular(model, X_val, out_dir)
    artifacts["shap"] = shap_path

    if len(X_val) > 0:
        sample = X_val.iloc[0]
        lime_path = lime_tabular(model, X_train, sample, out_dir, class_names=class_names)
        artifacts["lime"] = lime_path
    return artifacts


__all__ = ["shap_tabular", "lime_tabular", "lime_text", "export_tabular_explainability"]
