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
from keras import ops, random


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
    """Construct a simple VAE using a custom training loop (Keras 3 friendly)."""
    encoder_inputs = tf.keras.layers.Input(shape=(input_dim,), dtype="float32")
    x = tf.keras.layers.Dense(128, activation="relu")(encoder_inputs)
    z_mean = tf.keras.layers.Dense(latent_dim)(x)
    z_log_var = tf.keras.layers.Dense(latent_dim)(x)

    def sampling(args):
        z_mean_, z_log_var_ = args
        epsilon = random.normal(shape=(ops.shape(z_mean_)[0], latent_dim))
        return z_mean_ + ops.exp(0.5 * z_log_var_) * epsilon

    z = tf.keras.layers.Lambda(sampling, name="sampling")([z_mean, z_log_var])
    encoder = tf.keras.Model(encoder_inputs, [z_mean, z_log_var, z], name="encoder")

    decoder_input = tf.keras.layers.Input(shape=(latent_dim,))
    x_dec = tf.keras.layers.Dense(128, activation="relu")(decoder_input)
    outputs = tf.keras.layers.Dense(input_dim, activation="linear")(x_dec)
    decoder = tf.keras.Model(decoder_input, outputs, name="decoder")

    class VAE(tf.keras.Model):
        def __init__(self, encoder, decoder):
            super().__init__(name="vae")
            self.encoder = encoder
            self.decoder = decoder
            self.total_loss_tracker = tf.keras.metrics.Mean(name="loss")
            self.recon_loss_tracker = tf.keras.metrics.Mean(name="reconstruction_loss")
            self.kl_loss_tracker = tf.keras.metrics.Mean(name="kl_loss")

        @property
        def metrics(self):
            return [self.total_loss_tracker, self.recon_loss_tracker, self.kl_loss_tracker]

        def call(self, inputs):
            _, _, z = self.encoder(inputs)
            return self.decoder(z)

        def train_step(self, data):
            x = data[0] if isinstance(data, (list, tuple)) else data
            with tf.GradientTape() as tape:
                z_mean_, z_log_var_, z_ = self.encoder(x, training=True)
                reconstruction = self.decoder(z_, training=True)
                recon_loss = tf.reduce_mean(tf.reduce_sum(tf.square(x - reconstruction), axis=1))
                kl_loss = -0.5 * tf.reduce_mean(
                    tf.reduce_sum(1.0 + z_log_var_ - tf.square(z_mean_) - tf.exp(z_log_var_), axis=1)
                )
                total_loss = recon_loss + kl_loss
            grads = tape.gradient(total_loss, self.trainable_weights)
            self.optimizer.apply_gradients(zip(grads, self.trainable_weights))

            self.total_loss_tracker.update_state(total_loss)
            self.recon_loss_tracker.update_state(recon_loss)
            self.kl_loss_tracker.update_state(kl_loss)
            return {
                "loss": self.total_loss_tracker.result(),
                "reconstruction_loss": self.recon_loss_tracker.result(),
                "kl_loss": self.kl_loss_tracker.result(),
            }

        def test_step(self, data):
            x = data[0] if isinstance(data, (list, tuple)) else data
            z_mean_, z_log_var_, z_ = self.encoder(x, training=False)
            reconstruction = self.decoder(z_, training=False)
            recon_loss = tf.reduce_mean(tf.reduce_sum(tf.square(x - reconstruction), axis=1))
            kl_loss = -0.5 * tf.reduce_mean(
                tf.reduce_sum(1.0 + z_log_var_ - tf.square(z_mean_) - tf.exp(z_log_var_), axis=1)
            )
            total_loss = recon_loss + kl_loss
            self.total_loss_tracker.update_state(total_loss)
            self.recon_loss_tracker.update_state(recon_loss)
            self.kl_loss_tracker.update_state(kl_loss)
            return {
                "loss": self.total_loss_tracker.result(),
                "reconstruction_loss": self.recon_loss_tracker.result(),
                "kl_loss": self.kl_loss_tracker.result(),
            }

    vae = VAE(encoder, decoder)
    vae.compile(optimizer="adam", run_eagerly=True)
    return vae, decoder


def run_vae_pipeline(cfg: VAEConfig) -> Dict[str, float]:
    path = cfg.resolve_path()
    df = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
    df = df.select_dtypes(include=[np.number]).dropna()
    if df.empty:
        raise ValueError("No numeric columns available for VAE training.")

    scaler = StandardScaler()
    X = scaler.fit_transform(df.values).astype("float32")
    X_train, X_test = train_test_split(X, test_size=cfg.test_size, random_state=cfg.random_state)

    vae, decoder = _build_vae(input_dim=X.shape[1], latent_dim=cfg.latent_dim)
    history_logs = {
        "loss": [],
        "reconstruction_loss": [],
        "kl_loss": [],
        "val_loss": [],
        "val_reconstruction_loss": [],
        "val_kl_loss": [],
    }

    for epoch in range(cfg.epochs):
        perm = np.random.permutation(len(X_train))
        vae.reset_metrics()
        for start in range(0, len(X_train), cfg.batch_size):
            batch = X_train[perm[start : start + cfg.batch_size]]
            vae.train_step(batch)

        history_logs["loss"].append(float(vae.total_loss_tracker.result().numpy()))
        history_logs["reconstruction_loss"].append(float(vae.recon_loss_tracker.result().numpy()))
        history_logs["kl_loss"].append(float(vae.kl_loss_tracker.result().numpy()))

        vae.reset_metrics()
        val_logs = vae.test_step(X_test)
        history_logs["val_loss"].append(float(val_logs["loss"].numpy()))
        history_logs["val_reconstruction_loss"].append(float(val_logs["reconstruction_loss"].numpy()))
        history_logs["val_kl_loss"].append(float(val_logs["kl_loss"].numpy()))
        vae.reset_metrics()

    recon = vae(X_test, training=False).numpy()
    recon_error = np.mean(np.square(X_test - recon), axis=1)
    metrics = {
        "reconstruction_error_mean": float(np.mean(recon_error)),
        "reconstruction_error_std": float(np.std(recon_error)),
        "history": history_logs,
    }
    return metrics


__all__ = ["VAEConfig", "run_vae_pipeline"]
