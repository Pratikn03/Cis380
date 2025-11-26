"""Lightweight orchestration stubs for UAIS-V.

These wrappers call the existing experiment scripts so that references to
`src.orchestration.*` do not fail. They are intentionally thin to avoid heavy
dependencies—use the domain scripts/notebooks for full control.
"""

from .fraud_flow import fraud_pipeline
from .cyber_flow import cyber_pipeline
from .behavior_flow import behavior_pipeline
from .fusion_flow import fusion_pipeline
from .nlp_flow import nlp_pipeline
from .vision_flow import vision_pipeline

__all__ = [
    "fraud_pipeline",
    "cyber_pipeline",
    "behavior_pipeline",
    "fusion_pipeline",
    "nlp_pipeline",
    "vision_pipeline",
]
