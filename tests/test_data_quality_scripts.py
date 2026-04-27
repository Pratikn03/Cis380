from __future__ import annotations

import importlib
import json
import wave

import pandas as pd


def _load_module(module_name: str):
    return importlib.import_module(module_name)


def test_validate_catalog_reports_missing_paths(tmp_path, monkeypatch):
    validate_catalog = _load_module("scripts.data.validate_catalog")

    existing_dir = tmp_path / "exists"
    existing_dir.mkdir(parents=True)
    (existing_dir / "sample.txt").write_text("ok", encoding="utf-8")

    catalog = tmp_path / "datasets.yaml"
    catalog.write_text(
        """
datasets:
  - name: Existing
    domain: test
    path: "{existing_path}"
    license: mit
  - name: Missing
    domain: test
    path: "{missing_path}"
    license: mit
""".format(existing_path=existing_dir, missing_path=tmp_path / "missing"),
        encoding="utf-8",
    )

    report = validate_catalog.validate(catalog)
    assert report["status"] == "warning"
    assert report["dataset_count"] == 2
    assert any("missing path" in err for err in report["errors"])

    monkeypatch.chdir(tmp_path)
    validate_catalog.write_report(report)
    assert (tmp_path / "reports" / "data_catalog_report.json").exists()
    assert (tmp_path / "reports" / "data_catalog_report.md").exists()


def test_validate_dataset_counts_tabular_csv_files(tmp_path):
    validate_dataset = _load_module("scripts.data.validate_dataset")

    dataset_dir = tmp_path / "tabular" / "fraud"
    dataset_dir.mkdir(parents=True)
    (dataset_dir / "one.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    (dataset_dir / "two.csv").write_text("a,b\n3,4\n", encoding="utf-8")
    (dataset_dir / "ignore.txt").write_text("x", encoding="utf-8")

    count = validate_dataset.count_files(dataset_dir, validate_dataset.TAB_EXT)
    assert count == 2


def test_make_splits_csv_is_deterministic(tmp_path):
    make_splits = _load_module("scripts.data.make_splits")

    source_csv = tmp_path / "source.csv"
    pd.DataFrame(
        {
            "feature_a": list(range(1, 41)),
            "feature_b": [x * 2 for x in range(1, 41)],
            "label": [0 if x % 2 else 1 for x in range(1, 41)],
        }
    ).to_csv(source_csv, index=False)

    out_a = tmp_path / "split_a"
    out_b = tmp_path / "split_b"
    out_a.mkdir()
    out_b.mkdir()

    make_splits._split_csv(csv_path=source_csv, out_dir=out_a, seed=42, train=0.7, val=0.2)
    make_splits._split_csv(csv_path=source_csv, out_dir=out_b, seed=42, train=0.7, val=0.2)

    split_a = json.loads((out_a / "splits.json").read_text(encoding="utf-8"))
    split_b = json.loads((out_b / "splits.json").read_text(encoding="utf-8"))
    assert split_a["rows"] == split_b["rows"]
    assert (out_a / "train.csv").read_text(encoding="utf-8") == (out_b / "train.csv").read_text(
        encoding="utf-8"
    )


def test_make_splits_csv_stratifies_and_logs_duplicates(tmp_path):
    make_splits = _load_module("scripts.data.make_splits")

    rows = {
        "feature_a": list(range(100)) + [0],
        "label": ([0] * 50) + ([1] * 50) + [0],
    }
    source_csv = tmp_path / "source.csv"
    pd.DataFrame(rows).to_csv(source_csv, index=False)

    out_dir = tmp_path / "splits"
    manifest = tmp_path / "data" / "splits" / "fixture.json"
    make_splits._split_csv(
        csv_path=source_csv,
        out_dir=out_dir,
        seed=42,
        train=0.7,
        val=0.15,
        label_col="label",
        manifest_path=manifest,
    )

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["strategy"] == "stratified"
    assert payload["rows"]["excluded"] == 1
    assert payload["exclusions"][0]["reason"] == "duplicate"

    train_df = pd.read_csv(out_dir / "train.csv")
    val_df = pd.read_csv(out_dir / "val.csv")
    test_df = pd.read_csv(out_dir / "test.csv")
    assert set(train_df["label"]) == {0, 1}
    assert set(val_df["label"]) == {0, 1}
    assert set(test_df["label"]) == {0, 1}


def test_analyze_data_writes_one_screen_domain_audit(tmp_path):
    analyze_data = _load_module("analyze_data")

    domain = tmp_path / "data" / "raw" / "fraud"
    domain.mkdir(parents=True)
    (domain / "sample.csv").write_text(
        "Time,Amount,Class\n1,10,0\n2,,1\n2,,1\n",
        encoding="utf-8",
    )

    md_path, json_path = analyze_data.write_audit(domain)
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    text = md_path.read_text(encoding="utf-8")

    assert payload["row_count"] == 3
    assert payload["duplicate_rows"] == 1
    assert payload["target_column"] == "Class"
    assert "Class balance" in text


def test_training_data_audit_generates_reports(tmp_path):
    training_data_audit = _load_module("scripts.training_data_audit")

    # Minimal required tabular data
    fraud_csv = tmp_path / "data" / "raw" / "fraud" / "creditcard.csv"
    fraud_csv.parent.mkdir(parents=True, exist_ok=True)
    fraud_csv.write_text("Time,Amount,Class\n1,100.0,0\n2,20.0,1\n", encoding="utf-8")

    cyber_csv = tmp_path / "data" / "raw" / "cyber" / "UNSW_NB15_training-set.csv"
    cyber_csv.parent.mkdir(parents=True, exist_ok=True)
    cyber_csv.write_text("feature,label\n0.1,normal\n0.5,attack\n", encoding="utf-8")

    behavior_csv = tmp_path / "data" / "raw" / "behavior" / "online_shoppers_intention.csv"
    behavior_csv.parent.mkdir(parents=True, exist_ok=True)
    behavior_csv.write_text("Revenue,FeatureX\nTRUE,1\nFALSE,0\n", encoding="utf-8")

    # Minimal voice wav sample
    voice_dir = tmp_path / "data" / "raw" / "voice" / "happy"
    voice_dir.mkdir(parents=True, exist_ok=True)
    wav_path = voice_dir / "sample.wav"
    with wave.open(str(wav_path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(16000)
        handle.writeframes(b"\x00\x00" * 160)

    # Minimal prepared brand data
    prepared_root = tmp_path / "data" / "processed" / "brand_yolo"
    train_images = prepared_root / "train" / "images"
    val_images = prepared_root / "val" / "images"
    train_images.mkdir(parents=True, exist_ok=True)
    val_images.mkdir(parents=True, exist_ok=True)
    (train_images / "a.jpg").write_bytes(b"\xff\xd8\xff\xd9")
    (val_images / "b.jpg").write_bytes(b"\xff\xd8\xff\xd9")
    (prepared_root / "brands.yaml").write_text(
        "path: .\ntrain: train/images\nval: val/images\nnames:\n  - logo\n",
        encoding="utf-8",
    )

    training_data_audit.ROOT = tmp_path
    training_data_audit.REPORT_MD = tmp_path / "reports" / "TRAINING_DATA.md"
    training_data_audit.REPORT_JSON = tmp_path / "reports" / "TRAINING_DATA.json"

    code = training_data_audit.main()
    assert code == 0
    assert training_data_audit.REPORT_MD.exists()
    assert training_data_audit.REPORT_JSON.exists()
