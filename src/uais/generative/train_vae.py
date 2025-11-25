"""Tabular Variational Autoencoder utilities for UAIS generative experiments."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


@dataclass
class VAEConfig:
    dataset_path: Path
    latent_dim: int = 16
    epochs: int = 20
    batch_size: int = 128
    test_size: float = 0.2
    random_state: int = 42

    def resolve_path(self) -> Path:
        path = Path(self.dataset_path)
        if not path.exists():
            raise FileNotFoundError(f"Dataset not found for VAE training: {path}")
        return path


def _build_vae(input_dim: int, latent_dim: int) -> tf.keras.Model:
    inputs = tf.keras.layers.Input(shape=(input_dim,))
    x = tf.keras.layers.Dense(128, activation="relu")(inputs)
    z_mean = tf.keras.layers.Dense(latent_dim)(x)
    z_log_var = tf.keras.layers.Dense(latent_dim)(x)

    def sampling(args):
        z_mean_, z_log_var_ = args
        epsilon = tf.keras.backend.random_normal(shape=(tf.shape(z_mean_)[0], latent_dim))
        return z_mean_ + tf.exp(0.5 * z_log_var_) * epsilon

    z = tf.keras.layers.Lambda(sampling)([z_mean, z_log_var])
    decoder_input = tf.keras.layers.Input(shape=(latent_dim,))
    x_dec = tf.keras.layers.Dense(128, activation="relu")(decoder_input)
    outputs = tf.keras.layers.Dense(input_dim, activation="linear")(x_dec)
    decoder = tf.keras.Model(decoder_input, outputs, name="decoder")

    decoded = decoder(z)
    vae = tf.keras.Model(inputs, decoded, name="vae")

    reconstruction_loss = tf.keras.losses.mse(inputs, decoded)
    reconstruction_loss *= input_dim
    kl_loss = 1 + z_log_var - tf.square(z_mean) - tf.exp(z_log_var)
    kl_loss = -0.5 * tf.reduce_mean(kl_loss, axis=-1)
    vae.add_loss(tf.reduce_mean(reconstruction_loss + kl_loss))
    vae.compile(optimizer="adam")
    return vae, decoder


def run_vae_pipeline(cfg: VAEConfig) -> Dict[str, float]:
    path = cfg.resolve_path()
    df = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
    df = df.select_dtypes(include=[np.number]).dropna()
    if df.empty:
        raise ValueError("No numeric columns available for VAE training.")

    scaler = StandardScaler()
    X = scaler.fit_transform(df.values)
    X_train, X_test = train_test_split(X, test_size=cfg.test_size, random_state=cfg.random_state)

    vae, decoder = _build_vae(input_dim=X.shape[1], latent_dim=cfg.latent_dim)
    history = vae.fit(X_train, epochs=cfg.epochs, batch_size=cfg.batch_size, validation_data=(X_test, None))

    recon_error = np.mean(np.square(X_test - vae.predict(X_test, verbose=0)), axis=1)
    metrics = {
        "reconstruction_error_mean": float(np.mean(recon_error)),
        "reconstruction_error_std": float(np.std(recon_error)),
        "history": history.history,
    }
    return metrics


__all__ = ["VAEConfig", "run_vae_pipeline"]
