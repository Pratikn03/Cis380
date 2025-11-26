"""Training entrypoint for the 30-sequence model (PyTorch TCN or TensorFlow).

Reads data from data/sequences/X_30seq.npy/y_30seq.npy (builds if missing)
and trains either the torch TCN (default) or the TF model based on config.
Saves artifacts under artifacts/models/30seq/.
"""
from typing import Tuple

import numpy as np

from ..config import load_model_config, load_training_config
from ..data.build_30seq_dataset import build_30seq_arrays, load_30seq_arrays
from ..logging_utils import setup_logging
from ..paths import ARTIFACTS_DIR, SEQUENCES_DIR
from ..utils.seed import set_global_seed

logger = setup_logging(__name__)


def _maybe_load_data() -> Tuple[dict, np.ndarray]:
    if (SEQUENCES_DIR / "X_30seq.npy").exists() and (SEQUENCES_DIR / "y_30seq.npy").exists():
        logger.info("Loading existing 30-sequence arrays from %s", SEQUENCES_DIR)
        return load_30seq_arrays()

    logger.info("No prebuilt 30-sequence arrays found; generating synthetic/behavioral data.")
    return build_30seq_arrays()


def _train_torch(X_dict, y, train_cfg, model_cfg):
    from uais_v.training.train_30seq_torch import save_torch_model, train_torch_30seq

    model, metrics = train_torch_30seq(
        X_dict,
        y,
        batch_size=train_cfg.batch_size,
        epochs=train_cfg.epochs,
        lr=train_cfg.learning_rate,
        latent_dim=model_cfg.latent_dim,
        num_outputs=model_cfg.num_outputs,
    )
    out_dir = ARTIFACTS_DIR / "models" / "30seq"
    out_dir.mkdir(parents=True, exist_ok=True)
    model_path = out_dir / f"{train_cfg.model_name}.pt"
    save_torch_model(model, model_path)
    logger.info("Saved torch model to %s", model_path)
    return metrics


def _train_tf(X_dict, y, train_cfg, model_cfg):
    try:
        import tensorflow as tf
    except Exception as exc:  # pragma: no cover - optional dependency
        raise ImportError(
            "TensorFlow is required to train the 30-sequence TF model. Install tensorflow or tensorflow-cpu."
        ) from exc

    from uais_v.models.multi_sequence_30_tf import build_30_sequence_model

    model = build_30_sequence_model(
        seq_len=model_cfg.seq_len,
        n_features=model_cfg.n_features,
        latent_dim=model_cfg.latent_dim,
        num_outputs=model_cfg.num_outputs,
    )

    model.summary(print_fn=lambda x: logger.info(x))

    logger.info("Training (TensorFlow)...")
    history = model.fit(
        X_dict,
        y,
        batch_size=train_cfg.batch_size,
        epochs=train_cfg.epochs,
        validation_split=0.2,
        verbose=1,
    )

    out_dir = ARTIFACTS_DIR / "models" / "30seq"
    out_dir.mkdir(parents=True, exist_ok=True)
    model_path = out_dir / f"{train_cfg.model_name}.keras"
    model.save(model_path)
    logger.info("Saved TF model to %s", model_path)

    hist_path = out_dir / f"{train_cfg.model_name}_history.npy"
    np.save(hist_path, history.history)
    logger.info("Saved history to %s", hist_path)
    return {"train_loss": float(history.history.get("loss", [0])[-1])}


def main():  # pragma: no cover - entrypoint
    set_global_seed(42)
    train_cfg = load_training_config("training_30seq.yaml")
    model_cfg = load_model_config("model_30seq.yaml")

    logger.info("Loading 30-sequence data...")
    X_dict, y = _maybe_load_data()

    model_type = getattr(model_cfg, "type", "multi_sequence_30_tf").lower()
    if model_type == "multi_sequence_30_torch":
        metrics = _train_torch(X_dict, y, train_cfg, model_cfg)
    else:
        metrics = _train_tf(X_dict, y, train_cfg, model_cfg)

    logger.info("Training finished. Metrics: %s", metrics)


if __name__ == "__main__":  # pragma: no cover - CLI execution
    np.random.seed(42)
    main()
