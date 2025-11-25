import numpy as np


def test_fusion_keys_sorted_for_payload():
    # simple check for deterministic key ordering usage
    scores = {"cyber": 0.2, "fraud": 0.9, "behavior": 0.5}
    keys = sorted(scores)
    X = np.array([[scores[k] for k in keys]])
    assert X.shape == (1, 3)
