import os

import numpy as np
import pytest

RUN_TF_TESTS = os.getenv("RUN_TF_TESTS") == "1"
if not RUN_TF_TESTS:
    pytest.skip("Set RUN_TF_TESTS=1 to execute TensorFlow tests", allow_module_level=True)


def test_forward_pass_small_shape():
    pytest.importorskip("tensorflow", minversion="2.11")
    from uais_v.models.multi_sequence_30_tf import build_30_sequence_model

    model = build_30_sequence_model(seq_len=5, n_features=3, latent_dim=4, num_outputs=2)
    X = {f"seq_{i}": np.ones((2, 5, 3), dtype=np.float32) for i in range(1, 31)}
    out = model(X)
    assert out.shape == (2, 2)
