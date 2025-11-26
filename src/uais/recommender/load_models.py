"""Load models used by the recommender layer."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any

import joblib


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = PROJECT_ROOT / "models"
EXPERIMENTS_DIR = PROJECT_ROOT / "experiments"


def _load(path: Path):
    if not path.exists():
        return None
    try:
        return joblib.load(path)
    except Exception as exc:
        print(f"[load_models] Failed to load {path}: {exc}")
        return None


def load_all_models() -> Dict[str, Any]:
    """Return a dict with domain, fusion, and recommender models."""
    return {
        "fraud_model": _load(MODELS_DIR / "fraud" / "supervised" / "fraud_model.pkl"),
        "cyber_model": _load(MODELS_DIR / "cyber" / "supervised" / "cyber_model.pkl"),
        "behavior_lof": _load(MODELS_DIR / "behavior" / "behavior_lof.pkl"),
        "behavior_ae": _load(MODELS_DIR / "behavior" / "behavior_autoencoder.pkl"),
        "fusion": _load(EXPERIMENTS_DIR / "fusion" / "models" / "fusion_meta_model.pkl")
        or _load(MODELS_DIR / "fusion" / "fusion_meta_model.pkl"),
        "recommender": _load(MODELS_DIR / "recommender" / "recommender_model.pkl"),
    }


__all__ = ["load_all_models"]
