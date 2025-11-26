"""Train a simple recommender model based on domain/fusion scores."""
from __future__ import annotations

import json
import os
from typing import List, Dict, Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

from .feature_engineering import build_meta_features

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXPERIMENTS_DIR = os.path.join(PROJECT_ROOT, "experiments")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")


def _safe_read_csv(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        print(f"[train_recommender] WARNING: missing CSV: {path}")
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception as e:
        print(f"[train_recommender] ERROR reading {path}: {e}")
        return pd.DataFrame()


def _derive_action_label(label: int, fusion_score: float) -> str:
    """Heuristic mapping from (binary label, fusion risk) -> action."""
    if label == 1:
        if fusion_score >= 0.85:
            return "BLOCK"
        if fusion_score >= 0.7:
            return "REVIEW"
        return "MONITOR"
    else:
        if fusion_score >= 0.85:
            return "REVIEW"
        if fusion_score >= 0.6:
            return "MONITOR"
        return "ALLOW"


def _append_rows_from_scores(rows: List[Dict[str, Any]], df: pd.DataFrame, label_cols: List[str], score_cols: List[str], domain: str):
    if df.empty:
        return
    label_col = next((c for c in label_cols if c in df.columns), None)
    score_col = next((c for c in score_cols if c in df.columns), None)
    if not label_col or not score_col:
        print(f"[train_recommender] Could not find label/score columns in {domain} scores.")
        return
    for _, row in df.iterrows():
        y = int(row[label_col])
        s = float(row[score_col])
        scores = {"fraud": 0.0, "cyber": 0.0, "behavior": 0.0}
        scores[domain] = s
        scores["fusion"] = s
        action = _derive_action_label(y, scores["fusion"])
        meta_features, _ = build_meta_features(scores, event_features={})
        rows.append({"meta_features": meta_features, "action": action})


def build_training_rows() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    # FRAUD
    _append_rows_from_scores(
        rows,
        _safe_read_csv(os.path.join(EXPERIMENTS_DIR, "fraud", "scores.csv")),
        label_cols=["label", "y_true", "target"],
        score_cols=["supervised_score", "y_score", "pred_score", "prob_1", "score"],
        domain="fraud",
    )

    # CYBER
    _append_rows_from_scores(
        rows,
        _safe_read_csv(os.path.join(EXPERIMENTS_DIR, "cyber", "scores.csv")),
        label_cols=["label", "y_true", "target", "attack"],
        score_cols=["supervised_score", "y_score", "pred_score", "prob_1", "score"],
        domain="cyber",
    )

    # BEHAVIOR (unsupervised, use anomaly score)
    df_beh = _safe_read_csv(os.path.join(EXPERIMENTS_DIR, "behavior", "scores.csv"))
    if not df_beh.empty:
        score_col = next((c for c in ["anomaly_score", "lof_score", "score"] if c in df_beh.columns), None)
        if score_col:
            beh_vals = df_beh[score_col].values.astype(float)
            thr = np.quantile(beh_vals, 0.98) if len(beh_vals) > 0 else 0.9
            for _, row in df_beh.iterrows():
                beh_score = float(row[score_col])
                y = 1 if beh_score >= thr else 0
                scores = {"fraud": 0.0, "cyber": 0.0, "behavior": beh_score}
                scores["fusion"] = beh_score
                action = _derive_action_label(y, scores["fusion"])
                meta_features, _ = build_meta_features(scores, event_features={})
                rows.append({"meta_features": meta_features, "action": action})
        else:
            print("[train_recommender] No anomaly score column in behavior scores.")

    # FUSION (optional combined scores)
    df_fus = _safe_read_csv(os.path.join(EXPERIMENTS_DIR, "fusion", "fusion_scores.csv"))
    if not df_fus.empty:
        label_col = next((c for c in ["label", "y_true", "target"] if c in df_fus.columns), None)
        fraud_c = next((c for c in ["fraud", "fraud_score"] if c in df_fus.columns), None)
        cyber_c = next((c for c in ["cyber", "cyber_score"] if c in df_fus.columns), None)
        beh_c = next((c for c in ["behavior", "behavior_score"] if c in df_fus.columns), None)
        if label_col and fraud_c and cyber_c and beh_c:
            for _, row in df_fus.iterrows():
                y = int(row[label_col])
                scores = {
                    "fraud": float(row[fraud_c]),
                    "cyber": float(row[cyber_c]),
                    "behavior": float(row[beh_c]),
                }
                scores["fusion"] = float(np.mean([scores["fraud"], scores["cyber"], scores["behavior"]]))
                action = _derive_action_label(y, scores["fusion"])
                meta_features, _ = build_meta_features(scores, event_features={})
                rows.append({"meta_features": meta_features, "action": action})
        else:
            print("[train_recommender] Fusion scores CSV missing expected columns.")

    return rows


def main():
    rows = build_training_rows()
    if not rows:
        raise RuntimeError("No training rows constructed. Check experiments/*/scores.csv and column names.")

    X = np.stack([r["meta_features"] for r in rows], axis=0)
    y = np.array([r["action"] for r in rows])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        random_state=42,
        n_jobs=-1,
        class_weight="balanced",
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    report = classification_report(y_test, y_pred, output_dict=True)
    print(json.dumps(report, indent=2))

    os.makedirs(os.path.join(MODELS_DIR, "recommender"), exist_ok=True)
    model_path = os.path.join(MODELS_DIR, "recommender", "recommender_model.pkl")
    joblib.dump(clf, model_path)
    print(f"[train_recommender] Saved model to {model_path}")

    os.makedirs(os.path.join(EXPERIMENTS_DIR, "recommender", "metrics"), exist_ok=True)
    metrics_path = os.path.join(EXPERIMENTS_DIR, "recommender", "metrics", "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"[train_recommender] Saved metrics to {metrics_path}")


if __name__ == "__main__":
    main()
