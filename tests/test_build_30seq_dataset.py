import uais_v.data.build_30seq_dataset as b30


def test_build_sequences_writes_files(tmp_path, monkeypatch):
    monkeypatch.setattr(b30, "SEQUENCES_DIR", tmp_path)
    cfg = b30.SequenceBuildConfig(seq_len=6, n_features=4, anomaly_ratio=0.1, seed=7, min_events_per_entity=1)
    X_dict, y = b30.build_30seq_arrays(cfg)

    assert len(X_dict) == 30
    assert y.ndim == 1
    for arr in X_dict.values():
        assert arr.shape == (len(y), cfg.seq_len, cfg.n_features)
    assert (tmp_path / "X_30seq.npy").exists()
    assert (tmp_path / "y_30seq.npy").exists()
