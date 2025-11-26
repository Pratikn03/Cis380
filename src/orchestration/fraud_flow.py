"""Prefect flow for fraud data processing and training with MLflow logging and explainability.

Flow steps:
- Load raw fraud data
- Build features
- Train with train/val split
- Export scores/feature importances/SHAP for downstream fusion and dashboard
"""

import shutil

import mlflow
import numpy as np
import pandas as pd
from prefect import flow, task
from sklearn.model_selection import train_test_split

from uais.data.load_fraud_data import load_fraud_data
from uais.explainability.runner import export_tabular_explainability
from uais.features.fraud_features import build_fraud_feature_table
from uais.supervised.train_fraud_supervised import FraudModelConfig, train_fraud_model
from uais.utils.mlflow_utils import load_mlflow_settings, setup_mlflow
from uais.utils.paths import domain_paths
from uais.utils.stats import bootstrap_ci
from uais.supervised.train_fraud_supervised import cross_val_train_fraud
from uais.utils.runtime import time_block, measure_proba


@task
def load_data_task():
    return load_fraud_data()


@task
def feature_task(df):
    return build_fraud_feature_table(df)


@task
def train_task(df):
    target_col = "Class"
    X = df.drop(columns=[target_col])
    y = df[target_col]
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    # Correlation leak guard (warn if a feature is overly correlated with the target)
    corr = df.corr(numeric_only=True)[target_col].abs().sort_values(ascending=False)
    leak_features = [idx for idx, val in corr.items() if idx != target_col and val > 0.95]
    if leak_features:
        print(f"[warn] Potential leakage features with high correlation to target: {leak_features}")

    config = FraudModelConfig()
    train_time, (model, metrics) = time_block(
        train_fraud_model, X_train, y_train, X_val, y_val, config, True
    )

    mlflow.log_params(
        {
            "model_type": config.model_type,
            "max_depth": config.max_depth,
            "learning_rate": config.learning_rate,
            "max_iter": config.max_iter,
            "n_estimators": config.n_estimators,
        }
    )
    mlflow.log_metrics(metrics)
    mlflow.log_metric("train_time_sec", train_time)

    # Optional CV (fast 3-fold) for stability; write to metrics
    try:
        models_cv, cv_metrics = cross_val_train_fraud(X_train, y_train, config, n_splits=3, random_state=42)
        metrics.update(cv_metrics)
        mlflow.log_metrics(cv_metrics)
        # Write fold metrics to CSV
        scores = cv_metrics.get("cv_scores") if "cv_scores" in cv_metrics else None
        out_dir = domain_paths("fraud")["experiments"] / "metrics"
        out_dir.mkdir(parents=True, exist_ok=True)
        df_cv = pd.DataFrame({"fold_roc_auc": cv_metrics.get("cv_scores", [])})
        df_cv["mean"] = cv_metrics.get("cv_roc_auc_mean", np.nan)
        df_cv.to_csv(out_dir / "cv_metrics.csv", index=False)
    except Exception as exc:
        print(f"CV skipped: {exc}")

    # Export scores for fusion/explainability
    y_val_proba = model.predict_proba(X_val)[:, 1]
    from uais.utils.metrics import best_f1_threshold

    best_thr = best_f1_threshold(y_val.values, y_val_proba)
    mlflow.log_metric("best_f1_threshold", best_thr)

    # Bootstrap CI for ROC-AUC
    try:
        from sklearn.metrics import roc_auc_score
        lower, upper = bootstrap_ci(y_val.values, y_val_proba, roc_auc_score)
        metrics["roc_auc_ci_lower"] = lower
        metrics["roc_auc_ci_upper"] = upper
        mlflow.log_metric("roc_auc_ci_lower", lower)
        mlflow.log_metric("roc_auc_ci_upper", upper)
    except Exception as exc:
        print(f"CI computation skipped: {exc}")

    paths = domain_paths("fraud")
    scores_path = paths["experiments"] / "scores.csv"
    paths["experiments"].mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"score": y_val_proba, "label": y_val.values}).to_csv(scores_path, index=False)

    # Feature importances if available
    fi_path = paths["experiments"] / "feature_importances.csv"
    if hasattr(model, "feature_importances_"):
        fi = model.feature_importances_
    elif hasattr(model, "coef_"):
        fi = np.abs(model.coef_).ravel()
    else:
        fi = None
    if fi is not None:
        pd.DataFrame({"feature": X.columns, "importance": fi}).to_csv(fi_path, index=False)

    # Explainability artifacts (SHAP + LIME)
    try:
        explain_dir = paths["experiments"] / "explainability"
        explain_dir.mkdir(parents=True, exist_ok=True)
        artifacts = export_tabular_explainability(
            model, X_train, X_val, explain_dir, class_names=["normal", "fraud"]
        )
        plots_dir = paths["experiments"] / "plots"
        plots_dir.mkdir(parents=True, exist_ok=True)
        shap_path = artifacts.get("shap")
        lime_path = artifacts.get("lime")
        if shap_path:
            shutil.copy(shap_path, plots_dir / "shap_summary.png")
            mlflow.log_artifact(str(shap_path))
        if lime_path:
            shutil.copy(lime_path, plots_dir / "lime_tabular.txt")
            mlflow.log_artifact(str(lime_path))
    except Exception as exc:  # pragma: no cover - optional dep handling
        print(f"Explainability generation skipped: {exc}")

    # Runtime metrics
    try:
        proba_time = measure_proba(model, X_val, n_runs=10)
        runtime_dir = paths["experiments"] / "metrics"
        runtime_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(
            {"train_time_sec": [train_time], "predict_proba_sec_per_run": [proba_time]}
        ).to_csv(runtime_dir / "runtime.csv", index=False)
        mlflow.log_metric("predict_proba_sec_per_run", proba_time)
    except Exception as exc:
        print(f"Runtime logging skipped: {exc}")

    # Persist metrics for dashboard/aggregation
    metrics_dir = paths["experiments"] / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"Metric": list(metrics.keys()), "Value": list(metrics.values())}).to_csv(
        metrics_dir / "metrics.csv", index=False
    )

    return metrics.get("roc_auc", float("nan"))


@flow(name="Fraud Flow")
def fraud_pipeline():
    settings = load_mlflow_settings()
    setup_mlflow(experiment_name=settings["experiment_name"], tracking_uri=settings["tracking_uri"])

    with mlflow.start_run(run_name="fraud_flow"):
        df_raw = load_data_task()
        df_feat = feature_task(df_raw)
        auc = train_task(df_feat)
        print(f"Fraud pipeline completed. AUC: {auc:.4f}")


if __name__ == "__main__":
    fraud_pipeline()
