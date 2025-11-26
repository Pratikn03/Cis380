"""Prefect flow for behavior sequence models with MLflow logging and score export.

Flow steps:
- Load behavior data
- Build basic features
- Create sequences + mask
- Train LSTM classifier (CPU-friendly)
- Export scores and simple saliency for dashboard/fusion
"""

import shutil

import mlflow
import numpy as np
import pandas as pd
from prefect import flow, task
from sklearn.model_selection import train_test_split

from uais.data.load_behavior_data import load_behavior_data
from uais.features.behavior_features import build_behavior_feature_table
from uais.sequence.train_lstm import predict_lstm, train_lstm_classifier
from uais.sequence.evaluate_sequence import evaluate_sequence_predictions
from uais.explainability.sequence_explainer import sequence_saliency
from uais.utils.mlflow_utils import load_mlflow_settings, setup_mlflow
from uais.utils.paths import domain_paths
from uais.utils.stats import bootstrap_ci


@task
def load_data_task():
    return load_behavior_data()


@task
def feature_task(df):
    return build_behavior_feature_table(df)


@task
def prepare_sequences(df):
    target_col = "Revenue" if "Revenue" in df.columns else df.columns[-1]
    X = df.drop(columns=[target_col]).to_numpy(dtype=np.float32)
    y = df[target_col].to_numpy(dtype=np.int64)

    if len(X) < 5:
        raise ValueError("Behavior data too small to build sequences.")

    timesteps = min(10, len(X))
    usable = (len(X) // timesteps) * timesteps
    X_seq = X[:usable].reshape(-1, timesteps, X.shape[1])
    mask = np.ones((X_seq.shape[0], timesteps), dtype=np.float32)
    y_seq = y[:usable].reshape(-1, timesteps).max(axis=1)
    return X_seq, mask, y_seq


@task
def train_task(sequences, mask, labels):
    config = {"sequence": {"hidden_dim": 16, "batch_size": 32, "epochs": 4, "lr": 1e-3}}
    stratify_labels = labels if len(np.unique(labels)) > 1 else None
    X_train, X_val, mask_train, mask_val, y_train, y_val = train_test_split(
        sequences, mask, labels, test_size=0.2, stratify=stratify_labels, random_state=42
    )
    model, loss = train_lstm_classifier(X_train, mask_train, y_train, config)
    val_scores = predict_lstm(model, X_val, mask_val)

    # If labels are single-class (e.g., LDAP unsupervised), emit summary stats instead of supervised metrics.
    unique_labels = np.unique(y_val)
    if len(unique_labels) <= 1:
        metrics = {
            "mode": "unsupervised",
            "score_mean": float(np.mean(val_scores)),
            "score_std": float(np.std(val_scores)),
            "score_p95": float(np.quantile(val_scores, 0.95)),
            "positive_rate": float(np.mean(y_val)),
        }
    else:
        metrics = evaluate_sequence_predictions(y_val, val_scores)
    metrics["train_loss"] = loss

    mlflow.log_params({"hidden_dim": 16, "batch_size": 32, "epochs": 4, "lr": 1e-3})
    numeric_metrics = {k: float(v) for k, v in metrics.items() if isinstance(v, (int, float, np.floating))}
    if numeric_metrics:
        mlflow.log_metrics(numeric_metrics)

    # Export scores for fusion/explainability
    paths = domain_paths("behavior")
    paths["experiments"].mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"score": val_scores, "label": y_val}).to_csv(paths["experiments"] / "scores.csv", index=False)

    # Simple saliency export
    explain_dir = paths["experiments"] / "explainability"
    explain_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = paths["experiments"] / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    try:
        sal = sequence_saliency(X_val[:1], mask_val[:1])
        sal_path = explain_dir / "saliency.csv"
        pd.DataFrame({"timestep": list(sal.keys()), "saliency": list(sal.values())}).to_csv(
            sal_path, index=False
        )
        shutil.copy(sal_path, plots_dir / "saliency.csv")
        try:
            mlflow.log_artifact(str(sal_path))
        except Exception:
            pass
    except Exception as exc:  # pragma: no cover
        print(f"Saliency export skipped: {exc}")

    # Best-effort CV (3-fold) on sequences
    try:
        # simple CV by splitting sequences; no pipeline needed
        from sklearn.model_selection import StratifiedKFold
        skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
        aucs = []
        for train_idx, val_idx in skf.split(sequences, labels):
            X_tr, X_va = sequences[train_idx], sequences[val_idx]
            m_tr, m_va = mask[train_idx], mask[val_idx]
            y_tr, y_va = labels[train_idx], labels[val_idx]
            mdl, _ = train_lstm_classifier(X_tr, m_tr, y_tr, config)
            vs = predict_lstm(mdl, X_va, m_va)
            aucs.append(evaluate_sequence_predictions(y_va, vs).get("roc_auc", np.nan))
        metrics["cv_roc_auc_mean"] = float(np.nanmean(aucs)) if aucs else np.nan
        out_dir = paths["experiments"] / "metrics"
        out_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"fold_roc_auc": aucs, "mean": metrics.get("cv_roc_auc_mean", np.nan)}).to_csv(
            out_dir / "cv_metrics.csv", index=False
        )
    except Exception as exc:
        print(f"Behavior CV skipped: {exc}")

    # CI for ROC-AUC (best effort)
    try:
        from sklearn.metrics import roc_auc_score
        lower, upper = bootstrap_ci(y_val, val_scores, roc_auc_score)
        metrics["roc_auc_ci_lower"] = lower
        metrics["roc_auc_ci_upper"] = upper
    except Exception as exc:
        print(f"CI computation skipped: {exc}")

    # Persist metrics for dashboard/aggregation
    metrics_dir = domain_paths("behavior")["experiments"] / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"Metric": list(metrics.keys()), "Value": list(metrics.values())}).to_csv(
        metrics_dir / "metrics.csv", index=False
    )

    return metrics


@flow(name="Behavior Flow")
def behavior_pipeline():
    settings = load_mlflow_settings()
    setup_mlflow(experiment_name=settings["experiment_name"], tracking_uri=settings["tracking_uri"])

    with mlflow.start_run(run_name="behavior_flow"):
        df_raw = load_data_task()
        df_feat = feature_task(df_raw)
        sequences, mask, labels = prepare_sequences(df_feat)
        scores = train_task(sequences, mask, labels)
        print("Behavior sequence model completed. Metrics:", scores)


if __name__ == "__main__":
    behavior_pipeline()
