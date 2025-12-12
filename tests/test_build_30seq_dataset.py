import pandas as pd

import uais_v.data.build_30seq_dataset as b30


def test_build_sequences_writes_files(tmp_path, monkeypatch):
    monkeypatch.setattr(b30, "SEQUENCES_DIR", tmp_path)
    base_time = pd.date_range("2023-01-01", periods=12, freq="H")
    sample_df = pd.DataFrame(
        {
            "user": ["u1"] * 6 + ["u2"] * 6,
            "date": base_time,
            "content": ["hello world"] * 12,
            "filename": ["file.txt"] * 12,
            "pc": ["pc1"] * 12,
        }
    )
    monkeypatch.setattr(b30, "load_behavior_events", lambda path=None, n_rows=None: sample_df)
    cfg = b30.SequenceBuildConfig(seq_len=6, n_features=4, anomaly_ratio=0.1, seed=7, min_events_per_entity=1)
    X_dict, y = b30.build_30seq_arrays(cfg)

    assert len(X_dict) == 30
    assert y.ndim == 1
    for arr in X_dict.values():
        assert arr.shape == (len(y), cfg.seq_len, cfg.n_features)
    assert (tmp_path / "X_30seq.npy").exists()
    assert (tmp_path / "y_30seq.npy").exists()
