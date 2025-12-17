"""Placeholder cyber tabular model for UNSW-NB15 or similar datasets."""
from dataclasses import dataclass
from typing import Any

from .base_module import BaseModel


@dataclass
class CyberTabularModel(BaseModel):
    name: str = "cyber_tabular"

    def fit(self, X, y):  # pragma: no cover - placeholder
        raise NotImplementedError("CyberTabularModel.fit is not implemented.")

    def predict(self, X) -> Any:  # pragma: no cover - placeholder
        raise NotImplementedError("CyberTabularModel.predict is not implemented.")


__all__ = ["CyberTabularModel"]
