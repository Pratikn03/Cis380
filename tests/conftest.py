import os
import pathlib
import wave

os.environ["APP_ENV"] = "test"
os.environ["ALLOWED_HOSTS"] = "*"
os.environ["CORS_ORIGINS"] = "*"
os.environ["FORCE_HTTPS"] = "false"
os.environ["DATABASE_URL"] = "sqlite:///./data/test.db"
os.environ["SKIP_TORCH_PREIMPORT"] = "true"
os.environ.setdefault("AUTH_BYPASS", "true")

_wave_open = wave.open


def _path_supporting_wave_open(path, mode="rb", *args, **kwargs):
    if isinstance(path, pathlib.Path):
        path = str(path)
    return _wave_open(path, mode, *args, **kwargs)


wave.open = _path_supporting_wave_open
