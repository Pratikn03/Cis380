"""Vision anomaly detection helpers using TensorFlow/Keras.

The utilities keep training simple (a small CNN built with
``image_dataset_from_directory``). Replace the backbone with a ResNet/ViT later
if you need more accuracy.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import tensorflow as tf


@dataclass
class VisionConfig:
    dataset_dir: Path
    image_size: int = 224
    batch_size: int = 32
    epochs: int = 3
    validation_split: float = 0.2
    seed: int = 42

    def resolve_dir(self) -> Path:
        path = Path(self.dataset_dir)
        if not path.exists():
            raise FileNotFoundError(f"Vision dataset directory not found: {path}")
        return path


def _build_model(num_classes: int, image_size: int) -> tf.keras.Model:
    inputs = tf.keras.layers.Input(shape=(image_size, image_size, 3))
    x = tf.keras.layers.Rescaling(1.0 / 255)(inputs)
    x = tf.keras.layers.Conv2D(32, 3, activation="relu")(x)
    x = tf.keras.layers.MaxPooling2D()(x)
    x = tf.keras.layers.Conv2D(64, 3, activation="relu")(x)
    x = tf.keras.layers.MaxPooling2D()(x)
    x = tf.keras.layers.Conv2D(128, 3, activation="relu")(x)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax")(x)
    model = tf.keras.Model(inputs, outputs)
    model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    return model


def run_vision_experiment(cfg: VisionConfig) -> Dict[str, float]:
    data_dir = cfg.resolve_dir()
    train_ds = tf.keras.preprocessing.image_dataset_from_directory(
        data_dir,
        validation_split=cfg.validation_split,
        subset="training",
        seed=cfg.seed,
        image_size=(cfg.image_size, cfg.image_size),
        batch_size=cfg.batch_size,
    )
    val_ds = tf.keras.preprocessing.image_dataset_from_directory(
        data_dir,
        validation_split=cfg.validation_split,
        subset="validation",
        seed=cfg.seed,
        image_size=(cfg.image_size, cfg.image_size),
        batch_size=cfg.batch_size,
    )

    num_classes = len(train_ds.class_names)
    model = _build_model(num_classes=num_classes, image_size=cfg.image_size)

    history = model.fit(train_ds, validation_data=val_ds, epochs=cfg.epochs)
    eval_loss, eval_acc = model.evaluate(val_ds, verbose=0)
    metrics = {"val_loss": float(eval_loss), "val_accuracy": float(eval_acc), "history": history.history}
    return metrics


__all__ = ["VisionConfig", "run_vision_experiment"]
