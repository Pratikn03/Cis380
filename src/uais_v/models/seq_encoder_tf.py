"""TensorFlow sequence encoder used for 30-sequence model."""
try:
    import tensorflow as tf
    from tensorflow.keras import layers, Model
except Exception as exc:  # pragma: no cover - optional dependency
    raise ImportError(
        "TensorFlow is required for the 30-sequence model. Install tensorflow or tensorflow-cpu."
    ) from exc


def make_sequence_encoder(seq_len: int, n_features: int, latent_dim: int = 64) -> Model:
    inp = layers.Input(shape=(seq_len, n_features))
    x = layers.Masking()(inp)
    x = layers.LSTM(latent_dim, return_sequences=False)(x)
    x = layers.Dense(latent_dim, activation="relu")(x)
    return Model(inp, x, name=f"seq_encoder_{latent_dim}")


__all__ = ["make_sequence_encoder"]
