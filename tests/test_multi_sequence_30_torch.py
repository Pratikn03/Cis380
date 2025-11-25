import numpy as np
import pytest


def test_forward_pass_small_shape():
    torch = pytest.importorskip("torch")
    from uais_v.models.multi_sequence_30_torch import MultiSequenceTCNClassifier

    model = MultiSequenceTCNClassifier(seq_len=5, n_features=3, latent_dim=4, num_outputs=2)
    X = np.ones((2, 30, 5, 3), dtype=np.float32)
    out = model(torch.tensor(X))
    assert out.shape == (2, 2)
