"""Multi-sequence TensorFlow model that ties 30 encoders."""
try:
    import tensorflow as tf
    from tensorflow.keras import layers, Model
except Exception as exc:  # pragma: no cover - optional dependency
    raise ImportError(
        "TensorFlow is required for the 30-sequence model. Install tensorflow or tensorflow-cpu."
    ) from exc

from .seq_encoder_tf import make_sequence_encoder


def build_30_sequence_model(
    seq_len: int = 30,
    n_features: int = 16,
    latent_dim: int = 64,
    num_outputs: int = 2,
) -> Model:
    inputs = []
    encoded_outputs = []

    encoder = make_sequence_encoder(seq_len, n_features, latent_dim)

    for i in range(30):
        inp = layers.Input(shape=(seq_len, n_features), name=f"seq_{i+1}")
        inputs.append(inp)
        encoded = encoder(inp)
        encoded_outputs.append(encoded)

    merged = layers.Concatenate(name="concat_30seq")(encoded_outputs)
    x = layers.Dense(256, activation="relu")(merged)
    x = layers.Dropout(0.2)(x)
    x = layers.Dense(128, activation="relu")(x)

    if num_outputs == 1:
        activation = "sigmoid"
        loss = "binary_crossentropy"
    else:
        activation = "softmax"
        loss = "sparse_categorical_crossentropy"

    out = layers.Dense(num_outputs, activation=activation, name="output")(x)

    model = Model(inputs=inputs, outputs=out, name="multi_sequence_30")
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss=loss,
        metrics=["accuracy"],
    )
    return model


__all__ = ["build_30_sequence_model"]
