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

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff")


@dataclass
class VisionConfig:
    dataset_dir: Path
    image_size: int = 224
    batch_size: int = 32
    epochs: int = 3
    validation_split: float = 0.2
    seed: int = 42
    backbone: str = "simple_cnn"  # supported: simple_cnn, resnet50/resnet18

    def resolve_dir(self) -> Path:
        path = Path(self.dataset_dir)
        if not path.exists():
            raise FileNotFoundError(f"Vision dataset directory not found: {path}")
        return path


def _build_model(num_classes: int, image_size: int, backbone: str) -> tf.keras.Model:
    backbone = (backbone or "simple_cnn").lower()

    if backbone in {"resnet18", "resnet50", "resnet"}:
        inputs = tf.keras.layers.Input(shape=(image_size, image_size, 3))
        x = tf.keras.applications.resnet.preprocess_input(inputs)
        base = tf.keras.applications.ResNet50(
            include_top=False,
            weights="imagenet",
            input_shape=(image_size, image_size, 3),
            pooling="avg",
        )
        base.trainable = False
        x = base(x)
        outputs = tf.keras.layers.Dense(num_classes, activation="softmax")(x)
        model = tf.keras.Model(inputs, outputs)
        model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
        return model

    if backbone not in {"simple_cnn", ""}:
        raise ValueError(f"Unsupported backbone '{backbone}'. Use 'simple_cnn' or 'resnet50'.")

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


def _contains_images(directory: Path) -> bool:
    """Return True if the directory appears to contain image files."""
    if not directory.exists() or not directory.is_dir():
        return False
    for ext in IMAGE_EXTENSIONS:
        pattern = f"*{ext}"
        if next(directory.glob(pattern), None) is not None:
            return True
        if next(directory.glob(pattern.upper()), None) is not None:
            return True
    return False


def _normalize_dataset_root(directory: Path) -> Path:
    """Some Kaggle archives nest the actual class folders under an extra directory.

    If the provided directory only contains a single child directory that in turn
    has multiple subdirectories with images (e.g., seg_train/seg_train/*), point
    TensorFlow at that nested directory so class discovery works as expected.
    """
    if not directory.exists():
        return directory

    if _contains_images(directory):
        return directory

    subdirs = [d for d in directory.iterdir() if d.is_dir()]
    if len(subdirs) != 1:
        return directory

    candidate = subdirs[0]
    grandkids = [d for d in candidate.iterdir() if d.is_dir()]
    if not grandkids:
        return directory

    if any(_contains_images(grandchild) for grandchild in grandkids):
        return candidate

    return directory


def run_vision_experiment(cfg: VisionConfig) -> Dict[str, float]:
    resolved_dir = cfg.resolve_dir()
    data_dir = _normalize_dataset_root(resolved_dir)
    if data_dir != resolved_dir:
        print(f"Detected nested dataset directory. Using '{data_dir}' as the dataset root instead of '{resolved_dir}'.")
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
    model = _build_model(num_classes=num_classes, image_size=cfg.image_size, backbone=cfg.backbone)

    history = model.fit(train_ds, validation_data=val_ds, epochs=cfg.epochs)
    eval_loss, eval_acc = model.evaluate(val_ds, verbose=0)
    metrics = {"val_loss": float(eval_loss), "val_accuracy": float(eval_acc), "history": history.history}
    return metrics


__all__ = ["VisionConfig", "run_vision_experiment"]
