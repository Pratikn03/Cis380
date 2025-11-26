"""
Run a full fraud experiment end-to-end (v1).

Steps:
1. Load raw fraud data.
2. Build feature table.
3. Split into train/val/test.
4. Train supervised fraud model.
5. Evaluate and print metrics.
6. (Optional) Train Isolation Forest and compute a hybrid score.
"""

from pathlib import Path
import json
import joblib

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from uais.data.load_fraud_data import load_fraud_data
from uais.features.fraud_features import build_fraud_feature_table
from uais.supervised.train_fraud_supervised import FraudModelConfig, train_fraud_model
from uais.utils.metrics import compute_classification_metrics
from uais.utils.plotting import plot_roc_curve, plot_pr_curve
from uais.anomaly.train_isolation_forest import train_isolation_forest, compute_anomaly_score
from uais.ensembles.blending import blend_supervised_and_anomaly
from uais.utils.paths import domain_paths, ensure_directories


def main():
    ensure_directories()
    project_root = Path(__file__).resolve().parents[2]
    print(f"Project root: {project_root}")

    # 1. Load raw data
    df_raw = load_fraud_data()
    print(f"Loaded raw fraud data with shape: {df_raw.shape}")

    # 2. Build features
    df_feats = build_fraud_feature_table(df_raw, time_column="Time", amount_column="Amount", target_column="Class")
    print(f"Feature table shape: {df_feats.shape}")

    target_col = "Class"
    if target_col not in df_feats.columns:
        raise KeyError(f"Target column '{target_col}' not found in feature table.")

    X = df_feats.drop(columns=[target_col])
    y = df_feats[target_col].astype(int)

    # 3. Split into train/val/test (e.g., 60/20/20)
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.4, stratify=y, random_state=42
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, stratify=y_temp, random_state=42
    )

    print(f"Train shape: {X_train.shape}, Val shape: {X_val.shape}, Test shape: {X_test.shape}")

    # 4. Train supervised model
    config = FraudModelConfig(model_type="hist_gb", max_depth=4, learning_rate=0.1, max_iter=200)
    model, val_metrics = train_fraud_model(X_train, y_train, X_val, y_val, config)
    print("Validation metrics (supervised model):")
    for k, v in val_metrics.items():
        print(f"  {k}: {v:.4f}")

    # Evaluate on test set
    if hasattr(model, "predict_proba"):
        y_test_prob = model.predict_proba(X_test)[:, 1]
    else:
        scores = model.decision_function(X_test)
        y_test_prob = 1.0 / (1.0 + np.exp(-scores))

    test_metrics = compute_classification_metrics(y_test.values, y_test_prob, threshold=0.5)
    print("Test metrics (supervised model):")
    for k, v in test_metrics.items():
        print(f"  {k}: {v:.4f}")

    # Plot ROC and PR curves for test set
    experiments_dir = project_root / "experiments" / "fraud"
    plots_dir = experiments_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    plot_roc_curve(y_test.values, y_test_prob, title="Fraud ROC (Supervised)", show=False,
                   save_path=str(plots_dir / "roc_supervised.png"))
    plot_pr_curve(y_test.values, y_test_prob, title="Fraud PR (Supervised)", show=False,
                  save_path=str(plots_dir / "pr_supervised.png"))

    # 5. Train Isolation Forest on training data for anomaly scores (v1: use same features)
    iso_model, scaler = train_isolation_forest(X_train, contamination=0.01)
    anomaly_scores_test = compute_anomaly_score(iso_model, scaler, X_test)

    # 6. Compute blended / hybrid score
    hybrid_scores = blend_supervised_and_anomaly(y_test_prob, anomaly_scores_test, alpha=0.7, beta=0.3)

    hybrid_metrics = compute_classification_metrics(y_test.values, hybrid_scores, threshold=0.5)
    print("Test metrics (hybrid supervised + anomaly):")
    for k, v in hybrid_metrics.items():
        print(f"  {k}: {v:.4f}")

    plot_roc_curve(
        y_test.values,
        hybrid_scores,
        title="Fraud ROC (Hybrid)",
        show=False,
        save_path=str(plots_dir / "roc_hybrid.png"),
    )
    plot_pr_curve(
        y_test.values,
        hybrid_scores,
        title="Fraud PR (Hybrid)",
        show=False,
        save_path=str(plots_dir / "pr_hybrid.png"),
    )

    # Persist artifacts for dashboard/API/fusion
    paths = domain_paths("fraud")
    (paths["models"] / "supervised").mkdir(parents=True, exist_ok=True)
    joblib.dump(model, paths["models"] / "supervised" / "fraud_model.pkl")

    metrics_out = {
        "val": val_metrics,
        "test": test_metrics,
        "hybrid": hybrid_metrics,
    }
    metrics_dir = paths["experiments"] / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    with open(metrics_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics_out, f, indent=2)

    # Flatten key metrics for Streamlit convenience
    pd.DataFrame(
        [
            {"Metric": "test_roc_auc", "Value": test_metrics.get("roc_auc", float("nan"))},
            {"Metric": "test_f1", "Value": test_metrics.get("f1", float("nan"))},
            {"Metric": "hybrid_roc_auc", "Value": hybrid_metrics.get("roc_auc", float("nan"))},
            {"Metric": "hybrid_f1", "Value": hybrid_metrics.get("f1", float("nan"))},
        ]
    ).to_csv(metrics_dir / "metrics.csv", index=False)

    scores_dir = paths["experiments"]
    scores_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"score": y_test_prob, "label": y_test.values}).to_csv(scores_dir / "scores.csv", index=False)

    print("Experiment completed. Plots saved to:", plots_dir)
    print("Artifacts saved under:", paths["experiments"])


if __name__ == "__main__":
    main()
