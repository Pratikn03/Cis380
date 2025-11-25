import numpy as np


def test_generate_meta_features_and_train(tmp_path, monkeypatch):
    # synthetic scores and labels
    rng = np.random.default_rng(0)
    score_dict = {
        "fraud": rng.random(50),
        "cyber": rng.random(50),
        "behavior": rng.random(50),
    }
    labels = (rng.random(50) < 0.3).astype(int)

    from uais.fusion.build_embeddings import generate_meta_features
    X = generate_meta_features(score_dict)
    assert X.shape == (50, 3)

    # train fusion directly using train_fusion_meta_model helper
    from uais.fusion.train_fusion_model import train_fusion_meta_model

    config = {"seed": 0, "data": {"test_size": 0.2}}
    model, metrics = train_fusion_meta_model(score_dict, labels, config)
    assert "roc_auc" in metrics
    assert model.coef_.shape[1] == X.shape[1]
