from pathlib import Path

from src.vision.brand import recognizer


def test_development_registry_prefers_local_trained_logo_detector(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("BRAND_MODEL_LOGO_PATH", raising=False)
    monkeypatch.delenv("BRAND_MODEL_PATH", raising=False)
    local_model = Path("models/brand/full/weights/best.pt")
    local_model.parent.mkdir(parents=True)
    local_model.write_bytes(b"stub")

    assert recognizer.model_path("logo") == str(local_model)


def test_production_registry_keeps_release_artifact_path(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("BRAND_MODEL_LOGO_PATH", raising=False)
    monkeypatch.delenv("BRAND_MODEL_PATH", raising=False)
    local_model = Path("models/brand/full/weights/best.pt")
    local_model.parent.mkdir(parents=True)
    local_model.write_bytes(b"stub")

    assert recognizer.model_path("logo") == "artifacts/brand/yolo_logo_det.pt"
