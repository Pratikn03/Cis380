"""
==============================================================================
MULTIMODAL FUSION MODULE
==============================================================================
Author: Pratik Niroula
Project: Sentifargo - Sentifargo

PURPOSE:
--------
Combines signals from multiple modalities (vision, text, behavior, audio)
to provide unified recommendations and risk assessments.

FUSION STRATEGIES:
------------------
1. Early Fusion: Concatenate features before model
2. Late Fusion: Combine model outputs
3. Attention Fusion: Learned attention weights
4. Hierarchical Fusion: Multi-level combination

USAGE:
------
    from app.models.fusion.multimodal import MultimodalFusion
    
    fusion = MultimodalFusion()
    
    # Fuse multiple signals
    result = fusion.fuse(
        vision_features=image_embeddings,
        text_features=text_embeddings,
        behavior_features=user_history,
        audio_features=voice_emotion
    )
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from enum import Enum


class FusionStrategy(Enum):
    """Available fusion strategies."""
    EARLY = "early"           # Concatenate features
    LATE = "late"             # Average predictions
    WEIGHTED = "weighted"     # Weighted average
    ATTENTION = "attention"   # Learned attention
    HIERARCHICAL = "hierarchical"  # Multi-level


@dataclass
class ModalityInput:
    """Input from a single modality."""
    name: str                    # e.g., "vision", "text"
    features: Optional[np.ndarray]  # Feature vector
    prediction: Optional[float]     # Model prediction (0-1)
    confidence: float = 0.5      # Confidence in this modality
    weight: float = 1.0          # Importance weight
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class FusionResult:
    """Result of multimodal fusion."""
    fused_prediction: float
    fused_confidence: float
    modality_weights: Dict[str, float]
    modality_contributions: Dict[str, float]
    fusion_strategy: str
    details: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return asdict(self)


class MultimodalFusion:
    """
    Combines signals from multiple modalities for unified analysis.
    """
    
    # Default modality weights
    DEFAULT_WEIGHTS = {
        "vision": 1.0,
        "text": 0.8,
        "behavior": 0.9,
        "audio": 0.7,
        "tabular": 1.0,
    }
    
    def __init__(
        self,
        strategy: FusionStrategy = FusionStrategy.WEIGHTED,
        modality_weights: Optional[Dict[str, float]] = None
    ):
        """
        Initialize the fusion module.
        
        Args:
            strategy: Fusion strategy to use
            modality_weights: Custom weights for each modality
        """
        self.strategy = strategy
        self.modality_weights = modality_weights or self.DEFAULT_WEIGHTS.copy()
    
    def fuse(
        self,
        modalities: List[ModalityInput],
        strategy: Optional[FusionStrategy] = None
    ) -> FusionResult:
        """
        Fuse multiple modality inputs.
        
        Args:
            modalities: List of modality inputs
            strategy: Override default strategy
            
        Returns:
            FusionResult with combined prediction
        """
        strategy = strategy or self.strategy
        
        # Filter out modalities with no data
        active_modalities = [
            m for m in modalities 
            if m.features is not None or m.prediction is not None
        ]
        
        if not active_modalities:
            return FusionResult(
                fused_prediction=0.5,
                fused_confidence=0.0,
                modality_weights={},
                modality_contributions={},
                fusion_strategy=strategy.value,
                details={"error": "No valid modalities provided"}
            )
        
        # Apply fusion strategy
        if strategy == FusionStrategy.LATE:
            return self._late_fusion(active_modalities)
        elif strategy == FusionStrategy.WEIGHTED:
            return self._weighted_fusion(active_modalities)
        elif strategy == FusionStrategy.ATTENTION:
            return self._attention_fusion(active_modalities)
        elif strategy == FusionStrategy.EARLY:
            return self._early_fusion(active_modalities)
        elif strategy == FusionStrategy.HIERARCHICAL:
            return self._hierarchical_fusion(active_modalities)
        else:
            return self._weighted_fusion(active_modalities)
    
    def _late_fusion(self, modalities: List[ModalityInput]) -> FusionResult:
        """Simple average of predictions."""
        predictions = []
        confidences = []
        weights = {}
        
        for m in modalities:
            if m.prediction is not None:
                predictions.append(m.prediction)
                confidences.append(m.confidence)
                weights[m.name] = 1.0 / len(modalities)
        
        if not predictions:
            return self._empty_result("late")
        
        fused_pred = np.mean(predictions)
        fused_conf = np.mean(confidences)
        
        contributions = {
            m.name: m.prediction / (sum(predictions) + 1e-10)
            for m in modalities if m.prediction is not None
        }
        
        return FusionResult(
            fused_prediction=float(fused_pred),
            fused_confidence=float(fused_conf),
            modality_weights=weights,
            modality_contributions=contributions,
            fusion_strategy="late",
            details={"method": "simple_average", "num_modalities": len(predictions)}
        )
    
    def _weighted_fusion(self, modalities: List[ModalityInput]) -> FusionResult:
        """Weighted average based on modality importance."""
        weighted_sum = 0.0
        weight_total = 0.0
        conf_sum = 0.0
        weights = {}
        contributions = {}
        
        for m in modalities:
            if m.prediction is not None:
                # Get weight from config or use modality's own weight
                w = self.modality_weights.get(m.name, 1.0) * m.weight * m.confidence
                weighted_sum += m.prediction * w
                weight_total += w
                conf_sum += m.confidence * w
                weights[m.name] = w
        
        if weight_total == 0:
            return self._empty_result("weighted")
        
        fused_pred = weighted_sum / weight_total
        fused_conf = conf_sum / weight_total
        
        # Normalize weights
        weights = {k: v / weight_total for k, v in weights.items()}
        
        # Calculate contributions
        for m in modalities:
            if m.prediction is not None:
                contributions[m.name] = (
                    m.prediction * weights.get(m.name, 0)
                ) / (fused_pred + 1e-10)
        
        return FusionResult(
            fused_prediction=float(fused_pred),
            fused_confidence=float(fused_conf),
            modality_weights=weights,
            modality_contributions=contributions,
            fusion_strategy="weighted",
            details={"method": "weighted_average"}
        )
    
    def _attention_fusion(self, modalities: List[ModalityInput]) -> FusionResult:
        """Attention-based fusion using confidence as attention scores."""
        # Use confidence scores as attention weights
        confidences = np.array([m.confidence for m in modalities])
        predictions = np.array([m.prediction or 0.5 for m in modalities])
        
        # Softmax attention
        attention = np.exp(confidences) / np.sum(np.exp(confidences))
        
        fused_pred = np.sum(predictions * attention)
        fused_conf = np.sum(confidences * attention)
        
        weights = {m.name: float(attention[i]) for i, m in enumerate(modalities)}
        contributions = {m.name: float(predictions[i] * attention[i]) for i, m in enumerate(modalities)}
        
        return FusionResult(
            fused_prediction=float(fused_pred),
            fused_confidence=float(fused_conf),
            modality_weights=weights,
            modality_contributions=contributions,
            fusion_strategy="attention",
            details={"method": "softmax_attention", "attention_scores": attention.tolist()}
        )
    
    def _early_fusion(self, modalities: List[ModalityInput]) -> FusionResult:
        """Concatenate features and make unified prediction."""
        # Concatenate all features
        all_features = []
        feature_dims = {}
        
        for m in modalities:
            if m.features is not None:
                flat_features = m.features.flatten()
                all_features.append(flat_features)
                feature_dims[m.name] = len(flat_features)
        
        if not all_features:
            return self._empty_result("early")
        
        concatenated = np.concatenate(all_features)
        
        # Simple prediction: weighted average of feature magnitudes
        # (In practice, this would be a trained model)
        feature_mean = float(np.mean(np.abs(concatenated)))
        fused_pred = min(1.0, max(0.0, feature_mean))
        
        # Calculate weights based on feature dimension contribution
        total_dims = sum(feature_dims.values())
        weights = {k: v / total_dims for k, v in feature_dims.items()}
        
        return FusionResult(
            fused_prediction=fused_pred,
            fused_confidence=0.7,  # Fixed confidence for early fusion
            modality_weights=weights,
            modality_contributions=weights,  # Same as weights for early fusion
            fusion_strategy="early",
            details={
                "method": "feature_concatenation",
                "total_features": len(concatenated),
                "feature_dimensions": feature_dims
            }
        )
    
    def _hierarchical_fusion(self, modalities: List[ModalityInput]) -> FusionResult:
        """Multi-level hierarchical fusion."""
        # Group modalities by type
        perceptual = [m for m in modalities if m.name in ("vision", "audio")]
        cognitive = [m for m in modalities if m.name in ("text", "behavior")]
        other = [m for m in modalities if m.name not in ("vision", "audio", "text", "behavior")]
        
        results = []
        
        # First level: Fuse within groups
        if perceptual:
            perceptual_result = self._weighted_fusion(perceptual)
            results.append(ModalityInput(
                name="perceptual",
                features=None,
                prediction=perceptual_result.fused_prediction,
                confidence=perceptual_result.fused_confidence
            ))
        
        if cognitive:
            cognitive_result = self._weighted_fusion(cognitive)
            results.append(ModalityInput(
                name="cognitive",
                features=None,
                prediction=cognitive_result.fused_prediction,
                confidence=cognitive_result.fused_confidence
            ))
        
        if other:
            other_result = self._weighted_fusion(other)
            results.append(ModalityInput(
                name="other",
                features=None,
                prediction=other_result.fused_prediction,
                confidence=other_result.fused_confidence
            ))
        
        # Second level: Fuse group results
        if not results:
            return self._empty_result("hierarchical")
        
        final_result = self._weighted_fusion(results)
        final_result.fusion_strategy = "hierarchical"
        final_result.details["method"] = "two_level_hierarchical"
        final_result.details["groups"] = {
            "perceptual": [m.name for m in perceptual],
            "cognitive": [m.name for m in cognitive],
            "other": [m.name for m in other]
        }
        
        return final_result
    
    def _empty_result(self, strategy: str) -> FusionResult:
        """Return empty result when no valid data."""
        return FusionResult(
            fused_prediction=0.5,
            fused_confidence=0.0,
            modality_weights={},
            modality_contributions={},
            fusion_strategy=strategy,
            details={"error": "No valid predictions to fuse"}
        )
    
    def fuse_for_recommendation(
        self,
        vision_embedding: Optional[np.ndarray] = None,
        text_embedding: Optional[np.ndarray] = None,
        user_history: Optional[List[Dict]] = None,
        item_features: Optional[Dict] = None
    ) -> Tuple[np.ndarray, FusionResult]:
        """
        Create fused embedding for recommendation.
        
        Args:
            vision_embedding: Image embedding vector
            text_embedding: Text/query embedding
            user_history: User interaction history
            item_features: Item feature dict
            
        Returns:
            Tuple of (fused_embedding, fusion_result)
        """
        embeddings = []
        modalities = []
        
        # Vision
        if vision_embedding is not None:
            embeddings.append(vision_embedding)
            modalities.append(ModalityInput(
                name="vision",
                features=vision_embedding,
                prediction=None,
                confidence=0.9
            ))
        
        # Text
        if text_embedding is not None:
            embeddings.append(text_embedding)
            modalities.append(ModalityInput(
                name="text",
                features=text_embedding,
                prediction=None,
                confidence=0.8
            ))
        
        # User history -> embedding
        if user_history:
            # Simple: average of recent item embeddings (if available)
            history_embedding = np.zeros(128)  # Default embedding size
            modalities.append(ModalityInput(
                name="behavior",
                features=history_embedding,
                prediction=None,
                confidence=0.7
            ))
            embeddings.append(history_embedding)
        
        if not embeddings:
            return np.zeros(128), self._empty_result("recommendation")
        
        # Normalize and concatenate
        normalized = []
        for emb in embeddings:
            norm = np.linalg.norm(emb)
            if norm > 0:
                normalized.append(emb / norm)
            else:
                normalized.append(emb)
        
        # Weighted average (not concatenation for same-space fusion)
        weights = [self.modality_weights.get(m.name, 1.0) for m in modalities]
        weight_sum = sum(weights)
        
        fused = np.zeros_like(normalized[0])
        for emb, w in zip(normalized, weights):
            if emb.shape == fused.shape:
                fused += emb * (w / weight_sum)
            else:
                # Pad or truncate if different sizes
                min_len = min(len(emb), len(fused))
                fused[:min_len] += emb[:min_len] * (w / weight_sum)
        
        # Create fusion result
        result = FusionResult(
            fused_prediction=0.0,  # Not applicable for embeddings
            fused_confidence=np.mean([m.confidence for m in modalities]),
            modality_weights={m.name: weights[i] / weight_sum for i, m in enumerate(modalities)},
            modality_contributions={},
            fusion_strategy="embedding_weighted_average",
            details={
                "embedding_dim": len(fused),
                "modalities_used": [m.name for m in modalities]
            }
        )
        
        return fused, result


# Singleton instance
_fusion: Optional[MultimodalFusion] = None


def get_multimodal_fusion() -> MultimodalFusion:
    """Get or create the singleton fusion module."""
    global _fusion
    if _fusion is None:
        _fusion = MultimodalFusion()
    return _fusion


def fuse_predictions(
    vision: Optional[float] = None,
    text: Optional[float] = None,
    behavior: Optional[float] = None,
    audio: Optional[float] = None,
    strategy: str = "weighted"
) -> Dict[str, Any]:
    """
    Quick function to fuse predictions from multiple modalities.
    
    Args:
        vision: Vision model prediction (0-1)
        text: Text model prediction (0-1)
        behavior: Behavior model prediction (0-1)
        audio: Audio model prediction (0-1)
        strategy: Fusion strategy
        
    Returns:
        Dict with fused prediction and details
    """
    modalities = []
    
    if vision is not None:
        modalities.append(ModalityInput(name="vision", features=None, prediction=vision))
    if text is not None:
        modalities.append(ModalityInput(name="text", features=None, prediction=text))
    if behavior is not None:
        modalities.append(ModalityInput(name="behavior", features=None, prediction=behavior))
    if audio is not None:
        modalities.append(ModalityInput(name="audio", features=None, prediction=audio))
    
    fusion = get_multimodal_fusion()
    result = fusion.fuse(modalities, FusionStrategy(strategy))
    
    return result.to_dict()


__all__ = [
    "MultimodalFusion",
    "ModalityInput",
    "FusionResult",
    "FusionStrategy",
    "get_multimodal_fusion",
    "fuse_predictions",
]
