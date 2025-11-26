"""Helper to build fusion dataset from score files and train meta-model.

This is a thin wrapper around `train_fusion_meta_model` in train_fusion_model.py
so notebooks/scripts can easily load score CSVs and fit the stacker.
"""
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd

from uais.fusion.train_fusion_model import train_fusion_meta_model

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def build_fusion_dataset(score_paths: Dict[str, Path] | None = None) -> Tuple[Dict[str, np.ndarray], np.ndarray]:
    """Load per-domain score CSVs and align lengths.

    Expects each CSV to have at least a `score` column; `label` is optional.
    Uses the shortest length across domains to align scores.
    """
    if score_paths is None:
        score_paths = {
            "fraud": PROJECT_ROOT / "experiments" / "fraud" / "scores.csv",
            "cyber": PROJECT_ROOT / "experiments" / "cyber" / "scores.csv",
            "behavior": PROJECT_ROOT / "experiments" / "behavior" / "scores.csv",
            "vision": PROJECT_ROOT / "experiments" / "vision" / "scores.csv",
        }

    scores = {}
    labels = None
    for domain, path in score_paths.items():
        # Allow relative paths to be resolved from project root for notebooks/scripts.
        if not path.is_absolute():
            candidate = PROJECT_ROOT / path
            path = candidate if candidate.exists() else path

        if not path.exists():
            print(f"[warn] Score file missing for {domain}: {path}")
            continue
        df = pd.read_csv(path)
        if "score" not in df.columns:
            raise ValueError(f"Expected 'score' column in {path}")
        scores[domain] = df["score"].to_numpy()
        if labels is None and "label" in df.columns:
            labels = df["label"].to_numpy()

    if not scores:
        raise FileNotFoundError("No score files found for fusion.")

    min_len = min(len(v) for v in scores.values())
    scores = {k: v[:min_len] for k, v in scores.items()}
    if labels is None:
        labels = np.zeros(min_len, dtype=int)
    else:
        labels = labels[:min_len]

    return scores, labels


def train_fusion_model(score_paths: Dict[str, Path] | None = None, config: Dict | None = None):
    score_dict, labels = build_fusion_dataset(score_paths)
    config = config or {"data": {"test_size": 0.2}, "seed": 42}
    return train_fusion_meta_model(score_dict, labels, config)


__all__ = ["build_fusion_dataset", "train_fusion_model"]
