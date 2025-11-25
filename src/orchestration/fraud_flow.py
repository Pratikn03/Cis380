"""Prefect flow for fraud data processing and training."""

from prefect import flow, task

from uais.data.load_fraud_data import load_fraud_data
from uais.features.fraud_features import build_fraud_feature_table
from uais.supervised.train_fraud_supervised import FraudModelConfig, train_fraud_model


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
    config = FraudModelConfig()
    model, metrics = train_fraud_model(X, y, X, y, config)
    return metrics.get("roc_auc", float("nan"))


@flow(name="Fraud Flow")
def fraud_pipeline():
    df_raw = load_data_task()
    df_feat = feature_task(df_raw)
    auc = train_task(df_feat)
    print(f"Fraud pipeline completed. AUC: {auc:.4f}")


if __name__ == "__main__":
    fraud_pipeline()
