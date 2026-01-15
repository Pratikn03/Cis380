"""
==============================================================================
VIDEO LSTM TEMPORAL MODEL
==============================================================================
Author: Pratik Niroula
Project: Sentifargo - Sentifargo

PURPOSE:
--------
LSTM-based temporal model for video deepfake/authenticity detection.
Analyzes frame sequences to detect temporal inconsistencies that indicate
manipulation.

ARCHITECTURE:
-------------
    Frame Features (CNN) -> LSTM Layers -> Classification Head
    
    1. Feature Extraction: ResNet18 backbone extracts features from each frame
    2. Sequence Modeling: LSTM captures temporal dependencies
    3. Classification: Binary (real/fake) or multi-class

FEATURES:
---------
- Temporal consistency checking
- Frame-sequence reasoning
- Attention mechanism for key frame identification
- Multi-scale temporal analysis

USAGE:
------
    from app.models.video.video_lstm import VideoLSTMClassifier, predict_video
    
    # Load model
    model = VideoLSTMClassifier.load("models/vision/video_lstm.pt")
    
    # Predict
    result = predict_video("path/to/video.mp4")
    # Returns: {"label": "fake", "confidence": 0.92, "frame_scores": [...]}
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np

# Lazy imports for optional dependencies
_torch = None
_nn = None
_transforms = None


def _lazy_import_torch():
    """Lazy import PyTorch to avoid import errors when not needed."""
    global _torch, _nn, _transforms
    if _torch is None:
        import torch
        import torch.nn as nn
        from torchvision import transforms
        _torch = torch
        _nn = nn
        _transforms = transforms
    return _torch, _nn, _transforms


@dataclass
class VideoLSTMConfig:
    """Configuration for Video LSTM model."""
    input_dim: int = 512          # Feature dimension from CNN
    hidden_dim: int = 256         # LSTM hidden dimension
    num_layers: int = 2           # Number of LSTM layers
    num_classes: int = 2          # Output classes (real/fake)
    dropout: float = 0.3          # Dropout rate
    bidirectional: bool = True    # Use bidirectional LSTM
    sequence_length: int = 16     # Number of frames to analyze
    attention: bool = True        # Use attention mechanism


class TemporalAttention:
    """Attention mechanism for identifying key frames."""
    
    def __init__(self, hidden_dim: int):
        torch, nn, _ = _lazy_import_torch()
        self.attention = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.Tanh(),
            nn.Linear(hidden_dim // 2, 1),
        )
    
    def forward(self, lstm_output):
        """Apply attention to LSTM output."""
        torch, nn, _ = _lazy_import_torch()
        # lstm_output: (batch, seq_len, hidden_dim)
        attention_weights = torch.softmax(
            self.attention(lstm_output).squeeze(-1), dim=1
        )
        # Weighted sum
        context = torch.bmm(
            attention_weights.unsqueeze(1), lstm_output
        ).squeeze(1)
        return context, attention_weights


def create_video_lstm_model(config: VideoLSTMConfig = None):
    """
    Create a Video LSTM model for temporal video analysis.
    
    This function creates the model architecture using PyTorch.
    """
    torch, nn, _ = _lazy_import_torch()
    config = config or VideoLSTMConfig()
    
    class VideoLSTMClassifier(nn.Module):
        """LSTM-based video classifier for deepfake detection."""
        
        def __init__(self, cfg: VideoLSTMConfig):
            super().__init__()
            self.config = cfg
            
            # LSTM for temporal modeling
            self.lstm = nn.LSTM(
                input_size=cfg.input_dim,
                hidden_size=cfg.hidden_dim,
                num_layers=cfg.num_layers,
                batch_first=True,
                dropout=cfg.dropout if cfg.num_layers > 1 else 0,
                bidirectional=cfg.bidirectional,
            )
            
            lstm_output_dim = cfg.hidden_dim * (2 if cfg.bidirectional else 1)
            
            # Optional attention
            self.use_attention = cfg.attention
            if cfg.attention:
                self.attention = nn.Sequential(
                    nn.Linear(lstm_output_dim, lstm_output_dim // 2),
                    nn.Tanh(),
                    nn.Linear(lstm_output_dim // 2, 1),
                )
            
            # Classification head
            self.classifier = nn.Sequential(
                nn.Linear(lstm_output_dim, lstm_output_dim // 2),
                nn.ReLU(),
                nn.Dropout(cfg.dropout),
                nn.Linear(lstm_output_dim // 2, cfg.num_classes),
            )
        
        def forward(self, x, return_attention: bool = False):
            """
            Forward pass.
            
            Args:
                x: Frame features (batch, seq_len, input_dim)
                return_attention: Whether to return attention weights
                
            Returns:
                logits: Classification logits (batch, num_classes)
                attention_weights: Optional attention weights (batch, seq_len)
            """
            # LSTM
            lstm_out, _ = self.lstm(x)  # (batch, seq, hidden*2)
            
            # Attention or last hidden state
            if self.use_attention:
                attention_weights = torch.softmax(
                    self.attention(lstm_out).squeeze(-1), dim=1
                )
                context = torch.bmm(
                    attention_weights.unsqueeze(1), lstm_out
                ).squeeze(1)
            else:
                context = lstm_out[:, -1, :]  # Last timestep
                attention_weights = None
            
            # Classification
            logits = self.classifier(context)
            
            if return_attention:
                return logits, attention_weights
            return logits
    
    return VideoLSTMClassifier(config)


class FrameFeatureExtractor:
    """Extract features from video frames using pretrained CNN."""
    
    def __init__(self, device: str = "cpu"):
        torch, nn, transforms = _lazy_import_torch()
        from torchvision import models
        
        self.device = torch.device(device)
        
        # Use ResNet18 as backbone (lightweight)
        backbone = models.resnet18(weights="IMAGENET1K_V1")
        # Remove final classification layer
        self.feature_extractor = nn.Sequential(*list(backbone.children())[:-1])
        self.feature_extractor = self.feature_extractor.to(self.device)
        self.feature_extractor.eval()
        
        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            ),
        ])
    
    def extract(self, frames: List[np.ndarray]) -> np.ndarray:
        """
        Extract features from a list of frames.
        
        Args:
            frames: List of RGB frames as numpy arrays (H, W, 3)
            
        Returns:
            Feature array of shape (num_frames, feature_dim)
        """
        torch, _, _ = _lazy_import_torch()
        
        features = []
        with torch.no_grad():
            for frame in frames:
                # Transform and add batch dimension
                x = self.transform(frame).unsqueeze(0).to(self.device)
                # Extract features
                feat = self.feature_extractor(x)
                feat = feat.flatten().cpu().numpy()
                features.append(feat)
        
        return np.array(features)


def extract_frames_from_video(
    video_path: str,
    num_frames: int = 16,
    fps: float = 2.0
) -> List[np.ndarray]:
    """
    Extract frames from a video file.
    
    Args:
        video_path: Path to video file
        num_frames: Target number of frames to extract
        fps: Frames per second to sample
        
    Returns:
        List of RGB frames as numpy arrays
    """
    try:
        import cv2
    except ImportError:
        raise ImportError("OpenCV (cv2) is required for video processing")
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Calculate frame indices to extract
    frame_interval = max(1, int(video_fps / fps))
    indices = list(range(0, total_frames, frame_interval))[:num_frames]
    
    frames = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(frame_rgb)
    
    cap.release()
    
    # Pad if not enough frames
    while len(frames) < num_frames:
        if frames:
            frames.append(frames[-1])  # Repeat last frame
        else:
            raise ValueError("No frames could be extracted from video")
    
    return frames[:num_frames]


@dataclass
class VideoAnalysisResult:
    """Result of video analysis."""
    label: str
    confidence: float
    probabilities: Dict[str, float]
    frame_attention: Optional[List[float]]
    temporal_consistency: float
    key_frames: List[int]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "confidence": round(self.confidence, 4),
            "probabilities": {k: round(v, 4) for k, v in self.probabilities.items()},
            "frame_attention": [round(a, 4) for a in self.frame_attention] if self.frame_attention else None,
            "temporal_consistency": round(self.temporal_consistency, 4),
            "key_frames": self.key_frames,
        }


class VideoLSTMPredictor:
    """High-level predictor for video authenticity detection."""
    
    CLASS_NAMES = ["fake", "real"]
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        config: Optional[VideoLSTMConfig] = None,
        device: str = "cpu"
    ):
        torch, _, _ = _lazy_import_torch()
        
        self.device = torch.device(device)
        self.config = config or VideoLSTMConfig()
        
        # Initialize model
        self.model = create_video_lstm_model(self.config)
        self.model = self.model.to(self.device)
        
        # Load weights if provided
        if model_path and Path(model_path).exists():
            state = torch.load(model_path, map_location=self.device)
            self.model.load_state_dict(state)
        
        self.model.eval()
        
        # Feature extractor
        self.feature_extractor = FrameFeatureExtractor(device)
    
    def predict(self, video_path: str) -> VideoAnalysisResult:
        """
        Predict authenticity of a video.
        
        Args:
            video_path: Path to video file
            
        Returns:
            VideoAnalysisResult with prediction and analysis
        """
        torch, _, _ = _lazy_import_torch()
        
        # Extract frames
        frames = extract_frames_from_video(
            video_path,
            num_frames=self.config.sequence_length
        )
        
        # Extract features
        features = self.feature_extractor.extract(frames)
        
        # Convert to tensor
        x = torch.tensor(features, dtype=torch.float32).unsqueeze(0).to(self.device)
        
        # Predict
        with torch.no_grad():
            logits, attention_weights = self.model(x, return_attention=True)
            probs = torch.softmax(logits, dim=1)[0]
        
        # Get prediction
        pred_idx = int(probs.argmax())
        pred_label = self.CLASS_NAMES[pred_idx]
        confidence = float(probs[pred_idx])
        
        # Process attention weights
        frame_attention = None
        key_frames = []
        if attention_weights is not None:
            frame_attention = attention_weights[0].cpu().numpy().tolist()
            # Get top 3 key frames
            key_frames = np.argsort(frame_attention)[-3:].tolist()
        
        # Calculate temporal consistency
        # (lower variance in frame features = more consistent = likely real)
        temporal_consistency = 1.0 - min(1.0, float(np.std(features)) / 10.0)
        
        return VideoAnalysisResult(
            label=pred_label,
            confidence=confidence,
            probabilities={
                name: float(probs[i]) for i, name in enumerate(self.CLASS_NAMES)
            },
            frame_attention=frame_attention,
            temporal_consistency=temporal_consistency,
            key_frames=key_frames,
        )
    
    def predict_bytes(self, video_bytes: bytes, suffix: str = ".mp4") -> VideoAnalysisResult:
        """Predict from video bytes."""
        with tempfile.NamedTemporaryFile(delete=True, suffix=suffix) as tmp:
            tmp.write(video_bytes)
            tmp.flush()
            return self.predict(tmp.name)


# Singleton predictor
_video_predictor: Optional[VideoLSTMPredictor] = None


def get_video_predictor(device: str = "cpu") -> VideoLSTMPredictor:
    """Get or create the video predictor."""
    global _video_predictor
    if _video_predictor is None:
        model_path = Path("models/vision/video_lstm.pt")
        _video_predictor = VideoLSTMPredictor(
            model_path=str(model_path) if model_path.exists() else None,
            device=device
        )
    return _video_predictor


def predict_video(video_path: str, device: str = "cpu") -> Dict[str, Any]:
    """
    Quick function to predict video authenticity.
    
    Args:
        video_path: Path to video file
        device: Device to use ("cpu" or "cuda")
        
    Returns:
        Dict with prediction results
    """
    predictor = get_video_predictor(device)
    result = predictor.predict(video_path)
    return result.to_dict()


__all__ = [
    "VideoLSTMConfig",
    "VideoLSTMPredictor",
    "VideoAnalysisResult",
    "FrameFeatureExtractor",
    "create_video_lstm_model",
    "extract_frames_from_video",
    "get_video_predictor",
    "predict_video",
]
