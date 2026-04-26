import yaml

from src.vision.brand.data_utils import write_brands_yaml


def test_write_brands_yaml_uses_repo_relative_paths(tmp_path) -> None:
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    dataset_root = repo / "data" / "processed" / "brand_yolo"
    train_dir = dataset_root / "images" / "train"
    val_dir = dataset_root / "images" / "val"
    out_yaml = dataset_root / "brands.yaml"

    write_brands_yaml(out_yaml, train_dir, val_dir, ["logo"])

    payload = yaml.safe_load(out_yaml.read_text(encoding="utf-8"))
    assert payload["path"] == "data/processed/brand_yolo"
    assert payload["train"] == "images/train"
    assert payload["val"] == "images/val"
    assert payload["names"] == ["logo"]
