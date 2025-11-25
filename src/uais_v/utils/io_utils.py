"""Small IO helpers used by UAIS-V scripts."""
from pathlib import Path
from typing import Any, Dict
import json


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_json(data: Dict[str, Any], path: Path) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, indent=2))


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text())


__all__ = ["ensure_dir", "save_json", "load_json"]
