"""Placeholder fraud tabular model.

Use existing uais.supervised trainers or extend this stub.
"""
from dataclasses import dataclass
from typing import Any

from .base_module import BaseModel


@dataclass
class FraudTabularModel(BaseModel):
    name: str = "fraud_tabular"

    def fit(self, X, y):  # pragma: no cover - placeholder
        raise NotImplementedError("FraudTabularModel.fit is not implemented.")

    def predict(self, X) -> Any:  # pragma: no cover - placeholder
        raise NotImplementedError("FraudTabularModel.predict is not implemented.")


__all__ = ["FraudTabularModel"]
