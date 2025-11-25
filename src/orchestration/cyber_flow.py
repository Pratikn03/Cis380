"""Prefect flow for cyber intrusion modeling."""

from prefect import flow, task

from uais.data.load_cyber_data import load_cyber_data
from uais.features.cyber_features import build_cyber_feature_table
from uais.supervised.train_cyber_supervised import CyberModelConfig, train_cyber_model


@task
def load_data_task():
    return load_cyber_data()


@task
def feature_task(df):
    return build_cyber_feature_table(df)


@task
def train_task(df):
    target_col = "label"
    X = df.drop(columns=[target_col])
    y = df[target_col]
    config = CyberModelConfig()
    model, metrics = train_cyber_model(X, y, X, y, config)
    return metrics.get("accuracy", float("nan"))


@flow(name="Cyber Flow")
def cyber_pipeline():
    df_raw = load_data_task()
    df_feat = feature_task(df_raw)
    acc = train_task(df_feat)
    print(f"Cyber pipeline completed. Accuracy: {acc:.4f}")


if __name__ == "__main__":
    cyber_pipeline()
