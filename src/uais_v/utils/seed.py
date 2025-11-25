"""Seed helpers to make experiments reproducible."""
import os
import random
from typing import Optional

import numpy as np


def set_global_seed(seed: int, deterministic_torch: bool = False) -> None:
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

    try:
        import torch

        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        if deterministic_torch:
            torch.use_deterministic_algorithms(True)
    except Exception:
        # Torch is optional for UAIS-V
        pass

    try:
        import tensorflow as tf

        tf.random.set_seed(seed)
    except Exception:
        # TensorFlow is optional; skip if not installed
        pass


__all__ = ["set_global_seed"]
