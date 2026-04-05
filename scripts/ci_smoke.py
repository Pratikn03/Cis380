"""Tiny smoke check for CI.

Runs a lightweight fusion meta-model on synthetic scores to ensure imports
and basic training paths work without heavy dependencies.
"""

import numpy as np


def main() -> None:
    rng = np.random.default_rng(0)
    score_dict = {
        "fraud": rng.random(30),
        "cyber": rng.random(30),
        "behavior": rng.random(30),
    }
    labels = (rng.random(30) < 0.3).astype(int)

    from uais.fusion.train_fusion_model import train_fusion_meta_model

    config = {"seed": 0, "data": {"test_size": 0.2}}
    model, metrics = train_fusion_meta_model(score_dict, labels, config)
    print("[ci_smoke] metrics:", metrics)
    assert model.coef_.shape[1] == len(score_dict)


if __name__ == "__main__":
    main()
