"""Lightweight NLP text anomaly training utilities.

This module keeps dependencies minimal by using a TF-IDF + logistic regression
baseline. The ``model_name`` field exists so the notebook can display the
intended transformer backbone when you later swap in Hugging Face fine-tuning.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split


@dataclass
class NLPConfig:
    """Configuration for the text anomaly experiment."""

    dataset_path: Path
    text_column: str
    label_column: str
    model_name: str = "distilbert-base-uncased"
    max_samples: int = 10_000
    test_size: float = 0.2
    max_features: int = 5_000
    random_state: int = 42

    def resolve_path(self) -> Path:
        path = Path(self.dataset_path)
        if not path.exists():
            raise FileNotFoundError(f"Dataset not found: {path}")
        return path


def _load_dataset(cfg: NLPConfig) -> Tuple[pd.Series, pd.Series]:
    path = cfg.resolve_path()
    df = pd.read_csv(path)
    if cfg.text_column not in df.columns or cfg.label_column not in df.columns:
        raise KeyError(
            f"Columns '{cfg.text_column}' and '{cfg.label_column}' must exist in {path.name}."
        )
    df = df[[cfg.text_column, cfg.label_column]].dropna()
    if cfg.max_samples and len(df) > cfg.max_samples:
        df = df.sample(cfg.max_samples, random_state=cfg.random_state)
    return df[cfg.text_column], df[cfg.label_column]


def run_text_experiment(cfg: NLPConfig) -> Dict[str, float]:
    """Train a baseline TF-IDF + logistic regression model and return metrics."""

    texts, labels = _load_dataset(cfg)
    X_train, X_test, y_train, y_test = train_test_split(
        texts,
        labels,
        test_size=cfg.test_size,
        stratify=labels,
        random_state=cfg.random_state,
    )

    vectorizer = TfidfVectorizer(max_features=cfg.max_features)
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)

    clf = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=cfg.random_state)
    clf.fit(X_train_tfidf, y_train)

    y_prob = clf.predict_proba(X_test_tfidf)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)

    metrics: Dict[str, float] = {
        "roc_auc": float(roc_auc_score(y_test, y_prob)),
        "accuracy": float(np.mean(y_pred == y_test)),
    }

    print("Model:", cfg.model_name)
    print(classification_report(y_test, y_pred))
    return metrics


__all__ = ["NLPConfig", "run_text_experiment"]
