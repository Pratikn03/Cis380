"""Base module placeholder for UAIS-V models.

This is intentionally lightweight; extend as needed for specific domains.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class BaseModel:
    name: str = "model"

    def save(self, path: Path) -> None:  # pragma: no cover - simple passthrough
        raise NotImplementedError("Save is not implemented for the base stub.")

    @classmethod
    def load(cls, path: Path) -> "BaseModel":  # pragma: no cover - simple passthrough
        raise NotImplementedError("Load is not implemented for the base stub.")

    def predict(self, X: Any):  # pragma: no cover - simple passthrough
        raise NotImplementedError("Predict is not implemented for the base stub.")


__all__ = ["BaseModel"]
