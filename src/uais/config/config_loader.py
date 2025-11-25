"""Load and merge YAML configs."""
from pathlib import Path
from typing import Any, Dict

import yaml

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(domain: str, config_dir: Path = CONFIG_DIR) -> Dict[str, Any]:
    domain = domain.lower()
    base_cfg = _load_yaml(config_dir / "base_config.yaml")
    domain_cfg = _load_yaml(config_dir / f"{domain}_config.yaml")
    config = _deep_merge(base_cfg, domain_cfg)
    config["domain"] = domain
    config["config_dir"] = str(config_dir)
    return config


__all__ = ["load_config"]
