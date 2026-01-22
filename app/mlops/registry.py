"""
==============================================================================
MODEL REGISTRY - MLOps Model Versioning & Management
==============================================================================
Author: Pratik Niroula
Project: Sentifargo - Sentifargo

PURPOSE:
--------
Provides versioned model registry for tracking, deploying, and managing
ML models across the Sentifargo system.

FEATURES:
---------
- Model version control
- Metadata tracking (accuracy, training date, etc.)
- Model promotion (staging -> production)
- A/B testing support
- Rollback capability
- Integration with MLflow

USAGE:
------
    from app.mlops.registry import ModelRegistry
    
    registry = ModelRegistry()
    
    # Register a new model
    registry.register_model(
        name="fraud_detector",
        version="2.1.0",
        path="models/fraud/model_v2.pkl",
        metrics={"accuracy": 0.992, "f1": 0.85}
    )
    
    # Get production model
    model_info = registry.get_production_model("fraud_detector")
    
    # Promote to production
    registry.promote_model("fraud_detector", "2.1.0", "production")
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Literal
import hashlib
import threading


ModelStage = Literal["development", "staging", "production", "archived"]


@dataclass
class ModelVersion:
    """Information about a specific model version."""

    name: str
    version: str
    stage: ModelStage
    path: str
    created_at: str
    updated_at: str
    metrics: Dict[str, float] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)
    description: str = ""
    checksum: Optional[str] = None
    training_dataset: Optional[str] = None
    framework: str = "sklearn"

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "ModelVersion":
        return cls(**data)


@dataclass
class ModelInfo:
    """Information about a model (all versions)."""

    name: str
    description: str
    created_at: str
    latest_version: str
    production_version: Optional[str]
    staging_version: Optional[str]
    version_count: int
    tags: Dict[str, str] = field(default_factory=dict)


class ModelRegistry:
    """
    Registry for managing ML model versions and deployments.
    """

    STAGES: List[ModelStage] = ["development", "staging", "production", "archived"]

    def __init__(self, registry_dir: Optional[Path] = None):
        """
        Initialize the model registry.

        Args:
            registry_dir: Directory to store registry data
        """
        self.registry_dir = registry_dir or Path("mlops/registry")
        self.models_dir = self.registry_dir / "models"
        self.metadata_file = self.registry_dir / "registry.json"

        # Ensure directories exist
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Thread safety
        self._lock = threading.Lock()

        # Load existing registry
        self._registry: Dict[str, Dict[str, ModelVersion]] = {}
        self._load_registry()

    def _load_registry(self) -> None:
        """Load registry from disk."""
        if self.metadata_file.exists():
            try:
                data = json.loads(self.metadata_file.read_text())
                for model_name, versions in data.items():
                    self._registry[model_name] = {
                        ver: ModelVersion.from_dict(info) for ver, info in versions.items()
                    }
            except Exception:
                self._registry = {}

    def _save_registry(self) -> None:
        """Save registry to disk."""
        data = {
            model_name: {ver: mv.to_dict() for ver, mv in versions.items()}
            for model_name, versions in self._registry.items()
        }
        self.metadata_file.write_text(json.dumps(data, indent=2))

    def _compute_checksum(self, path: Path) -> str:
        """Compute SHA256 checksum of model file."""
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _now(self) -> str:
        """Get current timestamp."""
        return datetime.now().isoformat()

    def register_model(
        self,
        name: str,
        version: str,
        path: str,
        metrics: Optional[Dict[str, float]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
        description: str = "",
        training_dataset: Optional[str] = None,
        framework: str = "sklearn",
        stage: ModelStage = "development",
        copy_artifact: bool = True,
    ) -> ModelVersion:
        """
        Register a new model version.

        Args:
            name: Model name (e.g., "fraud_detector")
            version: Semantic version (e.g., "1.2.0")
            path: Path to model artifact
            metrics: Model performance metrics
            parameters: Training parameters
            tags: Additional tags
            description: Model description
            training_dataset: Dataset used for training
            framework: ML framework used
            stage: Initial stage
            copy_artifact: Whether to copy artifact to registry

        Returns:
            Registered ModelVersion
        """
        source_path = Path(path)
        if not source_path.exists():
            raise FileNotFoundError(f"Model artifact not found: {path}")

        with self._lock:
            # Check if version already exists
            if name in self._registry and version in self._registry[name]:
                raise ValueError(f"Version {version} already exists for model {name}")

            # Copy artifact to registry
            if copy_artifact:
                dest_dir = self.models_dir / name / version
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_path = dest_dir / source_path.name
                shutil.copy2(source_path, dest_path)
                artifact_path = str(dest_path)
            else:
                artifact_path = str(source_path)

            # Compute checksum
            checksum = self._compute_checksum(Path(artifact_path))

            # Create version entry
            model_version = ModelVersion(
                name=name,
                version=version,
                stage=stage,
                path=artifact_path,
                created_at=self._now(),
                updated_at=self._now(),
                metrics=metrics or {},
                parameters=parameters or {},
                tags=tags or {},
                description=description,
                checksum=checksum,
                training_dataset=training_dataset,
                framework=framework,
            )

            # Add to registry
            if name not in self._registry:
                self._registry[name] = {}
            self._registry[name][version] = model_version

            # Save
            self._save_registry()

            return model_version

    def get_model(self, name: str, version: str) -> Optional[ModelVersion]:
        """Get a specific model version."""
        with self._lock:
            if name in self._registry and version in self._registry[name]:
                return self._registry[name][version]
        return None

    def get_production_model(self, name: str) -> Optional[ModelVersion]:
        """Get the production version of a model."""
        with self._lock:
            if name not in self._registry:
                return None
            for version in self._registry[name].values():
                if version.stage == "production":
                    return version
        return None

    def get_staging_model(self, name: str) -> Optional[ModelVersion]:
        """Get the staging version of a model."""
        with self._lock:
            if name not in self._registry:
                return None
            for version in self._registry[name].values():
                if version.stage == "staging":
                    return version
        return None

    def get_latest_version(self, name: str) -> Optional[ModelVersion]:
        """Get the most recent version of a model."""
        with self._lock:
            if name not in self._registry:
                return None
            versions = list(self._registry[name].values())
            if not versions:
                return None
            # Sort by created_at descending
            versions.sort(key=lambda v: v.created_at, reverse=True)
            return versions[0]

    def list_models(self) -> List[ModelInfo]:
        """List all registered models."""
        with self._lock:
            result = []
            for name, versions in self._registry.items():
                if not versions:
                    continue

                sorted_versions = sorted(
                    versions.values(), key=lambda v: v.created_at, reverse=True
                )
                latest = sorted_versions[0]

                prod_version = next(
                    (v.version for v in versions.values() if v.stage == "production"), None
                )
                staging_version = next(
                    (v.version for v in versions.values() if v.stage == "staging"), None
                )

                result.append(
                    ModelInfo(
                        name=name,
                        description=latest.description,
                        created_at=min(v.created_at for v in versions.values()),
                        latest_version=latest.version,
                        production_version=prod_version,
                        staging_version=staging_version,
                        version_count=len(versions),
                        tags=latest.tags,
                    )
                )
            return result

    def list_versions(self, name: str) -> List[ModelVersion]:
        """List all versions of a model."""
        with self._lock:
            if name not in self._registry:
                return []
            return sorted(self._registry[name].values(), key=lambda v: v.created_at, reverse=True)

    def promote_model(self, name: str, version: str, target_stage: ModelStage) -> ModelVersion:
        """
        Promote a model to a new stage.

        Args:
            name: Model name
            version: Version to promote
            target_stage: Target stage (staging, production)

        Returns:
            Updated ModelVersion
        """
        with self._lock:
            if name not in self._registry:
                raise ValueError(f"Model {name} not found")
            if version not in self._registry[name]:
                raise ValueError(f"Version {version} not found for model {name}")

            # If promoting to production/staging, demote current holder
            if target_stage in ("production", "staging"):
                for ver in self._registry[name].values():
                    if ver.stage == target_stage and ver.version != version:
                        ver.stage = "archived" if target_stage == "production" else "development"
                        ver.updated_at = self._now()

            # Update target version
            model_version = self._registry[name][version]
            model_version.stage = target_stage
            model_version.updated_at = self._now()

            self._save_registry()
            return model_version

    def update_metrics(self, name: str, version: str, metrics: Dict[str, float]) -> ModelVersion:
        """Update metrics for a model version."""
        with self._lock:
            if name not in self._registry:
                raise ValueError(f"Model {name} not found")
            if version not in self._registry[name]:
                raise ValueError(f"Version {version} not found")

            model_version = self._registry[name][version]
            model_version.metrics.update(metrics)
            model_version.updated_at = self._now()

            self._save_registry()
            return model_version

    def delete_version(self, name: str, version: str, delete_artifact: bool = False) -> bool:
        """Delete a model version."""
        with self._lock:
            if name not in self._registry:
                return False
            if version not in self._registry[name]:
                return False

            model_version = self._registry[name][version]

            # Don't delete production models
            if model_version.stage == "production":
                raise ValueError("Cannot delete production model. Demote first.")

            # Optionally delete artifact
            if delete_artifact:
                artifact_path = Path(model_version.path)
                if artifact_path.exists():
                    artifact_path.unlink()

            # Remove from registry
            del self._registry[name][version]
            if not self._registry[name]:
                del self._registry[name]

            self._save_registry()
            return True

    def compare_versions(self, name: str, version1: str, version2: str) -> Dict[str, Any]:
        """Compare metrics between two versions."""
        with self._lock:
            if name not in self._registry:
                raise ValueError(f"Model {name} not found")

            v1 = self._registry[name].get(version1)
            v2 = self._registry[name].get(version2)

            if not v1 or not v2:
                raise ValueError("One or both versions not found")

            # Compare metrics
            all_metrics = set(v1.metrics.keys()) | set(v2.metrics.keys())
            comparison = {}

            for metric in all_metrics:
                val1 = v1.metrics.get(metric)
                val2 = v2.metrics.get(metric)

                if val1 is not None and val2 is not None:
                    diff = val2 - val1
                    pct_change = (diff / val1 * 100) if val1 != 0 else 0
                    better = diff > 0  # Assuming higher is better
                else:
                    diff = None
                    pct_change = None
                    better = None

                comparison[metric] = {
                    "version1": val1,
                    "version2": val2,
                    "difference": diff,
                    "percent_change": pct_change,
                    "improved": better,
                }

            return {
                "model": name,
                "version1": version1,
                "version2": version2,
                "metrics_comparison": comparison,
                "v1_stage": v1.stage,
                "v2_stage": v2.stage,
            }

    def get_summary(self) -> Dict[str, Any]:
        """Get registry summary statistics."""
        with self._lock:
            total_models = len(self._registry)
            total_versions = sum(len(v) for v in self._registry.values())

            stage_counts = {"development": 0, "staging": 0, "production": 0, "archived": 0}
            for versions in self._registry.values():
                for ver in versions.values():
                    stage_counts[ver.stage] += 1

            return {
                "total_models": total_models,
                "total_versions": total_versions,
                "by_stage": stage_counts,
                "models_in_production": stage_counts["production"],
                "models_in_staging": stage_counts["staging"],
            }


# Singleton instance
_registry: Optional[ModelRegistry] = None


def get_model_registry() -> ModelRegistry:
    """Get or create the singleton model registry."""
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry


__all__ = [
    "ModelRegistry",
    "ModelVersion",
    "ModelInfo",
    "ModelStage",
    "get_model_registry",
]
