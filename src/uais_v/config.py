"""Configuration loaders for UAIS-V."""
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml

from .paths import CONFIG_DIR


@dataclass
class TrainingConfig:
    batch_size: int
    epochs: int
    learning_rate: float
    model_name: str = "model"


@dataclass
class ModelConfig:
    type: str
    seq_len: int
    n_features: int
    latent_dim: int
    num_outputs: int = 2


def _resolve_config_path(name: str) -> Path:
    path = Path(name)
    if not path.suffix:
        path = path.with_suffix(".yaml")
    if not path.is_absolute():
        path = CONFIG_DIR / path
    return path


def load_yaml_config(name: str) -> Dict[str, Any]:
    path = _resolve_config_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_training_config(name: str = "training_30seq.yaml") -> TrainingConfig:
    cfg = load_yaml_config(name)
    if "training" not in cfg:
        raise KeyError(f"Missing 'training' section in {name}")
    return TrainingConfig(**cfg["training"])


def load_model_config(name: str = "model_30seq.yaml") -> ModelConfig:
    cfg = load_yaml_config(name)
    if "model" not in cfg:
        raise KeyError(f"Missing 'model' section in {name}")
    return ModelConfig(**cfg["model"])


__all__ = [
    "TrainingConfig",
    "ModelConfig",
    "load_yaml_config",
    "load_training_config",
    "load_model_config",
]
