"""Prefect flow for CERT behavior sequence models."""

from prefect import flow, task

from uais.data.load_behavior_data import load_behavior_data
from uais.features.cert_behavior_features import build_behavior_feature_table
from uais.sequence.train_lstm import train_lstm_autoencoder


@task
def load_data_task():
    return load_behavior_data()


@task
def feature_task(df):
    return build_behavior_feature_table(df)


@task
def train_task(sequences):
    return train_lstm_autoencoder(sequences)


@flow(name="Behavior Flow")
def behavior_pipeline():
    df_raw = load_data_task()
    df_feat = feature_task(df_raw)
    feat_array = df_feat.values
    if feat_array.size == 0:
        raise ValueError("Behavior features are empty.")
    timesteps = min(10, len(feat_array))
    usable = (len(feat_array) // timesteps) * timesteps
    sequences = feat_array[:usable].reshape(-1, timesteps, feat_array.shape[1])
    train_task(sequences)
    print("Behavior sequence model completed.")


if __name__ == "__main__":
    behavior_pipeline()
