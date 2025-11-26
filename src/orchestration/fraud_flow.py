"""Prefect flow for fraud data processing and training with MLflow logging and explainability.

Flow steps:
- Load raw fraud data
- Build features
- Train with train/val split
- Export scores/feature importances/SHAP for downstream fusion and dashboard
"""

import mlflow
import numpy as np
import pandas as pd
from prefect import flow, task
from sklearn.model_selection import train_test_split

from uais.data.load_fraud_data import load_fraud_data
from uais.features.fraud_features import build_fraud_feature_table
from uais.supervised.train_fraud_supervised import FraudModelConfig, train_fraud_model
from uais.utils.mlflow_utils import load_mlflow_settings, setup_mlflow
from uais.utils.paths import domain_paths


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
    model, metrics = train_fraud_model(X_train, y_train, X_val, y_val, config)

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

    # Export scores for fusion/explainability
    y_val_proba = model.predict_proba(X_val)[:, 1]
    from uais.utils.metrics import best_f1_threshold

    best_thr = best_f1_threshold(y_val.values, y_val_proba)
    mlflow.log_metric("best_f1_threshold", best_thr)

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

    # SHAP summary plot (best effort)
    try:
        import shap  # noqa: F401
        import matplotlib.pyplot as plt

        sample = X_val.sample(n=min(200, len(X_val)), random_state=42)
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(sample)
        plots_dir = paths["experiments"] / "plots"
        plots_dir.mkdir(parents=True, exist_ok=True)
        plt.figure()
        shap.summary_plot(shap_values, sample, show=False)
        plt.tight_layout()
        plt.savefig(plots_dir / "shap_summary.png", dpi=150)
        plt.close()
    except Exception as exc:  # pragma: no cover - optional dep handling
        print(f"SHAP generation skipped: {exc}")

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
