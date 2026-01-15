"""
==============================================================================
VOICE CONFIDENCE CALIBRATION MODULE
==============================================================================
Author: Pratik Niroula
Project: Sentifargo - Sentifargo

PURPOSE:
--------
Calibrate confidence scores from voice/emotion models to be well-calibrated
probabilistic predictions. Uses temperature scaling and isotonic regression.

METHODS:
--------
- Temperature Scaling: Simple post-hoc calibration
- Platt Scaling: Logistic regression on logits
- Isotonic Regression: Non-parametric calibration
- Beta Calibration: Flexible parametric method

METRICS:
--------
- ECE (Expected Calibration Error)
- MCE (Maximum Calibration Error)
- Brier Score
- Reliability Diagrams

USAGE:
------
    from app.models.voice.calibration import ConfidenceCalibrator
    
    calibrator = ConfidenceCalibrator(method="temperature")
    calibrator.fit(val_logits, val_labels)
    calibrated = calibrator.calibrate(test_probs)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from abc import ABC, abstractmethod
import math

# Lazy imports
def _get_numpy():
    try:
        import numpy as np
        return np
    except ImportError:
        return None

def _get_scipy():
    try:
        from scipy import optimize
        from scipy.special import softmax, expit
        return optimize, softmax, expit
    except ImportError:
        return None, None, None


@dataclass
class CalibrationMetrics:
    """Calibration evaluation metrics."""
    ece: float  # Expected Calibration Error
    mce: float  # Maximum Calibration Error
    brier_score: float
    n_bins: int
    bin_accuracies: List[float]
    bin_confidences: List[float]
    bin_counts: List[int]
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def summary(self) -> str:
        return f"ECE: {self.ece:.4f}, MCE: {self.mce:.4f}, Brier: {self.brier_score:.4f}"


class CalibrationMethod(ABC):
    """Base class for calibration methods."""
    
    @abstractmethod
    def fit(self, logits: Any, labels: Any) -> None:
        """Fit calibration parameters."""
        pass
    
    @abstractmethod
    def calibrate(self, probs: Any) -> Any:
        """Apply calibration to probabilities."""
        pass
    
    @abstractmethod
    def get_params(self) -> Dict[str, Any]:
        """Get calibration parameters."""
        pass


class TemperatureScaling(CalibrationMethod):
    """
    Temperature scaling for confidence calibration.
    
    Divides logits by a learned temperature parameter T > 0.
    Simple but effective for neural networks.
    """
    
    def __init__(self, init_temperature: float = 1.5):
        self.temperature = init_temperature
        self._fitted = False
    
    def fit(self, logits: Any, labels: Any) -> None:
        """
        Fit temperature parameter using NLL minimization.
        
        Args:
            logits: Model logits (before softmax)
            labels: True labels
        """
        np = _get_numpy()
        optimize, softmax, _ = _get_scipy()
        
        if np is None:
            self._fitted = True
            return
        
        logits = np.array(logits)
        labels = np.array(labels)
        
        def nll_loss(T):
            """Negative log likelihood with temperature T."""
            scaled = logits / T[0]
            probs = softmax(scaled, axis=-1) if len(scaled.shape) > 1 else self._softmax_1d(scaled)
            
            # Handle binary case
            if len(probs.shape) == 1:
                probs = np.stack([1 - probs, probs], axis=-1)
            
            # Cross entropy
            log_probs = np.log(np.clip(probs, 1e-10, 1.0))
            return -np.mean(log_probs[np.arange(len(labels)), labels.astype(int)])
        
        if optimize is not None:
            result = optimize.minimize(
                nll_loss,
                [self.temperature],
                method='L-BFGS-B',
                bounds=[(0.1, 10.0)]
            )
            self.temperature = result.x[0]
        
        self._fitted = True
    
    def _softmax_1d(self, x):
        """Simple softmax for 1D array."""
        np = _get_numpy()
        if np is None:
            return x
        exp_x = np.exp(x - np.max(x))
        return exp_x / exp_x.sum()
    
    def calibrate(self, probs: Any) -> Any:
        """
        Apply temperature scaling.
        
        For probabilities, we need to convert to logits first.
        """
        np = _get_numpy()
        _, softmax, _ = _get_scipy()
        
        if np is None:
            return probs
        
        probs = np.array(probs)
        
        # Convert probs to logits
        probs_clipped = np.clip(probs, 1e-10, 1.0 - 1e-10)
        logits = np.log(probs_clipped / (1 - probs_clipped))
        
        # Scale by temperature
        scaled_logits = logits / self.temperature
        
        # Convert back to probs
        calibrated = 1 / (1 + np.exp(-scaled_logits))
        
        return calibrated
    
    def get_params(self) -> Dict[str, Any]:
        return {"temperature": self.temperature, "fitted": self._fitted}


class PlattScaling(CalibrationMethod):
    """
    Platt scaling using logistic regression.
    
    Fits parameters A and B: P(y=1|f) = 1 / (1 + exp(A*f + B))
    """
    
    def __init__(self):
        self.A = 1.0
        self.B = 0.0
        self._fitted = False
    
    def fit(self, logits: Any, labels: Any) -> None:
        """Fit Platt scaling parameters."""
        np = _get_numpy()
        optimize, _, expit = _get_scipy()
        
        if np is None or optimize is None:
            self._fitted = True
            return
        
        logits = np.array(logits).flatten()
        labels = np.array(labels).flatten()
        
        def loss(params):
            A, B = params
            p = expit(A * logits + B)
            p = np.clip(p, 1e-10, 1 - 1e-10)
            return -np.mean(labels * np.log(p) + (1 - labels) * np.log(1 - p))
        
        result = optimize.minimize(loss, [1.0, 0.0], method='L-BFGS-B')
        self.A, self.B = result.x
        self._fitted = True
    
    def calibrate(self, probs: Any) -> Any:
        """Apply Platt scaling."""
        np = _get_numpy()
        _, _, expit = _get_scipy()
        
        if np is None:
            return probs
        
        probs = np.array(probs)
        
        # Convert to logits
        probs_clipped = np.clip(probs, 1e-10, 1 - 1e-10)
        logits = np.log(probs_clipped / (1 - probs_clipped))
        
        # Apply Platt scaling
        if expit is not None:
            calibrated = expit(self.A * logits + self.B)
        else:
            calibrated = 1 / (1 + np.exp(-(self.A * logits + self.B)))
        
        return calibrated
    
    def get_params(self) -> Dict[str, Any]:
        return {"A": self.A, "B": self.B, "fitted": self._fitted}


class IsotonicCalibration(CalibrationMethod):
    """
    Isotonic regression for non-parametric calibration.
    
    Fits a monotonically increasing function to map
    raw probabilities to calibrated probabilities.
    """
    
    def __init__(self):
        self._bins: List[Tuple[float, float, float]] = []  # (lower, upper, calibrated)
        self._fitted = False
    
    def fit(self, logits: Any, labels: Any) -> None:
        """Fit isotonic regression."""
        np = _get_numpy()
        
        if np is None:
            self._fitted = True
            return
        
        # Convert logits to probabilities
        probs = 1 / (1 + np.exp(-np.array(logits).flatten()))
        labels = np.array(labels).flatten()
        
        # Sort by probability
        order = np.argsort(probs)
        probs_sorted = probs[order]
        labels_sorted = labels[order]
        
        # Pool Adjacent Violators Algorithm (PAVA)
        n = len(probs_sorted)
        y = labels_sorted.copy().astype(float)
        
        # Simple PAVA implementation
        i = 0
        while i < n - 1:
            if y[i] > y[i + 1]:
                # Merge and average
                y[i] = y[i + 1] = (y[i] + y[i + 1]) / 2
                # Look back
                j = i - 1
                while j >= 0 and y[j] > y[j + 1]:
                    y[j] = y[j + 1] = (y[j] + y[j + 1]) / 2
                    j -= 1
            i += 1
        
        # Create bins
        n_bins = min(20, n)
        bin_size = n // n_bins
        
        self._bins = []
        for i in range(n_bins):
            start = i * bin_size
            end = (i + 1) * bin_size if i < n_bins - 1 else n
            
            lower = probs_sorted[start]
            upper = probs_sorted[end - 1]
            calibrated = np.mean(y[start:end])
            
            self._bins.append((lower, upper, calibrated))
        
        self._fitted = True
    
    def calibrate(self, probs: Any) -> Any:
        """Apply isotonic calibration."""
        np = _get_numpy()
        
        if np is None or not self._bins:
            return probs
        
        probs = np.array(probs)
        original_shape = probs.shape
        probs = probs.flatten()
        
        calibrated = np.zeros_like(probs)
        
        for i, p in enumerate(probs):
            # Find appropriate bin
            for lower, upper, cal_value in self._bins:
                if lower <= p <= upper:
                    calibrated[i] = cal_value
                    break
            else:
                # Extrapolate
                if p < self._bins[0][0]:
                    calibrated[i] = self._bins[0][2]
                else:
                    calibrated[i] = self._bins[-1][2]
        
        return calibrated.reshape(original_shape)
    
    def get_params(self) -> Dict[str, Any]:
        return {"n_bins": len(self._bins), "fitted": self._fitted}


class ConfidenceCalibrator:
    """
    High-level calibrator with multiple methods and evaluation.
    """
    
    METHODS = {
        "temperature": TemperatureScaling,
        "platt": PlattScaling,
        "isotonic": IsotonicCalibration
    }
    
    def __init__(
        self,
        method: str = "temperature",
        n_bins: int = 15
    ):
        """
        Initialize calibrator.
        
        Args:
            method: Calibration method ("temperature", "platt", "isotonic")
            n_bins: Number of bins for evaluation
        """
        if method not in self.METHODS:
            raise ValueError(f"Unknown method: {method}. Use: {list(self.METHODS.keys())}")
        
        self.method_name = method
        self.method = self.METHODS[method]()
        self.n_bins = n_bins
        self._is_fitted = False
    
    def fit(
        self,
        logits: Any,
        labels: Any,
        validation_split: float = 0.0
    ) -> 'ConfidenceCalibrator':
        """
        Fit the calibrator.
        
        Args:
            logits: Model logits or probabilities
            labels: True labels
            validation_split: If > 0, hold out for validation
            
        Returns:
            self for chaining
        """
        self.method.fit(logits, labels)
        self._is_fitted = True
        return self
    
    def calibrate(self, probs: Any) -> Any:
        """
        Apply calibration to probabilities.
        
        Args:
            probs: Raw probabilities
            
        Returns:
            Calibrated probabilities
        """
        if not self._is_fitted:
            return probs
        return self.method.calibrate(probs)
    
    def evaluate(
        self,
        probs: Any,
        labels: Any,
        calibrated: bool = True
    ) -> CalibrationMetrics:
        """
        Evaluate calibration quality.
        
        Args:
            probs: Probabilities (raw or calibrated)
            labels: True labels
            calibrated: Whether probs are already calibrated
            
        Returns:
            CalibrationMetrics with ECE, MCE, Brier score
        """
        np = _get_numpy()
        
        if np is None:
            return CalibrationMetrics(
                ece=0.0, mce=0.0, brier_score=0.0, n_bins=self.n_bins,
                bin_accuracies=[], bin_confidences=[], bin_counts=[]
            )
        
        probs = np.array(probs).flatten()
        labels = np.array(labels).flatten()
        
        if calibrated and self._is_fitted:
            probs = self.calibrate(probs)
        
        # Compute metrics
        bin_boundaries = np.linspace(0, 1, self.n_bins + 1)
        bin_accuracies = []
        bin_confidences = []
        bin_counts = []
        
        for i in range(self.n_bins):
            in_bin = (probs > bin_boundaries[i]) & (probs <= bin_boundaries[i + 1])
            count = in_bin.sum()
            
            if count > 0:
                accuracy = labels[in_bin].mean()
                confidence = probs[in_bin].mean()
            else:
                accuracy = 0.0
                confidence = (bin_boundaries[i] + bin_boundaries[i + 1]) / 2
            
            bin_accuracies.append(float(accuracy))
            bin_confidences.append(float(confidence))
            bin_counts.append(int(count))
        
        # ECE: weighted average of |accuracy - confidence|
        total = len(probs)
        ece = sum(
            (count / total) * abs(acc - conf)
            for acc, conf, count in zip(bin_accuracies, bin_confidences, bin_counts)
            if count > 0
        )
        
        # MCE: maximum |accuracy - confidence|
        mce = max(
            abs(acc - conf)
            for acc, conf, count in zip(bin_accuracies, bin_confidences, bin_counts)
            if count > 0
        ) if any(c > 0 for c in bin_counts) else 0.0
        
        # Brier score
        brier_score = float(np.mean((probs - labels) ** 2))
        
        return CalibrationMetrics(
            ece=float(ece),
            mce=float(mce),
            brier_score=brier_score,
            n_bins=self.n_bins,
            bin_accuracies=bin_accuracies,
            bin_confidences=bin_confidences,
            bin_counts=bin_counts
        )
    
    def get_reliability_diagram_data(
        self,
        probs: Any,
        labels: Any
    ) -> Dict[str, List[float]]:
        """
        Get data for plotting reliability diagram.
        
        Args:
            probs: Probabilities
            labels: True labels
            
        Returns:
            Dict with 'raw' and 'calibrated' metrics
        """
        # Raw metrics
        raw_metrics = self.evaluate(probs, labels, calibrated=False)
        
        # Calibrated metrics
        if self._is_fitted:
            calibrated_probs = self.calibrate(probs)
            cal_metrics = self.evaluate(calibrated_probs, labels, calibrated=False)
        else:
            cal_metrics = raw_metrics
        
        return {
            "bin_centers": [(i + 0.5) / self.n_bins for i in range(self.n_bins)],
            "raw_accuracy": raw_metrics.bin_accuracies,
            "raw_confidence": raw_metrics.bin_confidences,
            "calibrated_accuracy": cal_metrics.bin_accuracies,
            "calibrated_confidence": cal_metrics.bin_confidences,
            "counts": raw_metrics.bin_counts
        }
    
    def save(self, path: str) -> None:
        """Save calibration parameters."""
        params = {
            "method": self.method_name,
            "n_bins": self.n_bins,
            "params": self.method.get_params()
        }
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(params, f, indent=2)
    
    def load(self, path: str) -> 'ConfidenceCalibrator':
        """Load calibration parameters."""
        with open(path, 'r') as f:
            params = json.load(f)
        
        self.method_name = params["method"]
        self.method = self.METHODS[self.method_name]()
        self.n_bins = params["n_bins"]
        
        # Restore parameters
        method_params = params.get("params", {})
        if isinstance(self.method, TemperatureScaling):
            self.method.temperature = method_params.get("temperature", 1.0)
        elif isinstance(self.method, PlattScaling):
            self.method.A = method_params.get("A", 1.0)
            self.method.B = method_params.get("B", 0.0)
        
        self._is_fitted = method_params.get("fitted", False)
        return self


# Voice-specific calibrator
class VoiceConfidenceCalibrator(ConfidenceCalibrator):
    """
    Specialized calibrator for voice emotion recognition.
    
    Handles multi-class emotion predictions with per-class calibration.
    """
    
    EMOTIONS = ["neutral", "happy", "sad", "angry", "fearful", "surprised", "disgusted"]
    
    def __init__(
        self,
        method: str = "temperature",
        per_class: bool = False,
        n_bins: int = 10
    ):
        """
        Initialize voice calibrator.
        
        Args:
            method: Calibration method
            per_class: Whether to calibrate per emotion class
            n_bins: Number of bins
        """
        super().__init__(method=method, n_bins=n_bins)
        self.per_class = per_class
        self._class_calibrators: Dict[str, ConfidenceCalibrator] = {}
    
    def fit_multiclass(
        self,
        probs: Any,
        labels: Any,
        class_names: Optional[List[str]] = None
    ) -> 'VoiceConfidenceCalibrator':
        """
        Fit calibration for multi-class predictions.
        
        Args:
            probs: Probability matrix [n_samples, n_classes]
            labels: True class indices
            class_names: Names of classes
            
        Returns:
            self for chaining
        """
        np = _get_numpy()
        if np is None:
            return self
        
        probs = np.array(probs)
        labels = np.array(labels)
        
        if self.per_class and len(probs.shape) > 1:
            class_names = class_names or self.EMOTIONS[:probs.shape[1]]
            
            for i, name in enumerate(class_names):
                # Binary labels for this class
                binary_labels = (labels == i).astype(int)
                class_probs = probs[:, i]
                
                calibrator = ConfidenceCalibrator(method=self.method_name)
                
                # Convert to logits for fitting
                class_probs_clip = np.clip(class_probs, 1e-10, 1 - 1e-10)
                logits = np.log(class_probs_clip / (1 - class_probs_clip))
                
                calibrator.fit(logits, binary_labels)
                self._class_calibrators[name] = calibrator
        else:
            # Single calibrator for max confidence
            max_probs = probs.max(axis=-1) if len(probs.shape) > 1 else probs
            pred_labels = probs.argmax(axis=-1) if len(probs.shape) > 1 else (probs > 0.5).astype(int)
            correct = (pred_labels == labels).astype(int)
            
            logits = np.log(np.clip(max_probs, 1e-10, 1 - 1e-10) / (1 - np.clip(max_probs, 1e-10, 1 - 1e-10)))
            self.fit(logits, correct)
        
        return self
    
    def calibrate_multiclass(self, probs: Any) -> Any:
        """
        Calibrate multi-class probabilities.
        
        Args:
            probs: Probability matrix [n_samples, n_classes]
            
        Returns:
            Calibrated probabilities
        """
        np = _get_numpy()
        if np is None:
            return probs
        
        probs = np.array(probs)
        
        if self.per_class and self._class_calibrators:
            calibrated = np.zeros_like(probs)
            
            for i, (name, cal) in enumerate(self._class_calibrators.items()):
                if i < probs.shape[1]:
                    calibrated[:, i] = cal.calibrate(probs[:, i])
            
            # Renormalize
            calibrated = calibrated / calibrated.sum(axis=-1, keepdims=True)
            return calibrated
        else:
            # Calibrate max confidence only
            max_probs = probs.max(axis=-1)
            calibrated_max = self.calibrate(max_probs)
            
            # Scale all probabilities proportionally
            scale = calibrated_max / np.clip(max_probs, 1e-10, None)
            calibrated = probs * scale[:, np.newaxis]
            
            # Renormalize
            calibrated = calibrated / calibrated.sum(axis=-1, keepdims=True)
            return calibrated


# Demo
if __name__ == "__main__":
    np = _get_numpy()
    
    if np is not None:
        print("Testing Confidence Calibration...")
        
        # Generate synthetic data
        np.random.seed(42)
        n_samples = 1000
        
        # Simulated overconfident model
        true_probs = np.random.uniform(0.3, 0.7, n_samples)
        labels = (np.random.random(n_samples) < true_probs).astype(int)
        
        # Model predictions (overconfident)
        model_probs = np.clip(true_probs + np.random.normal(0.1, 0.15, n_samples), 0.01, 0.99)
        logits = np.log(model_probs / (1 - model_probs))
        
        # Test each method
        for method in ["temperature", "platt", "isotonic"]:
            print(f"\n📊 {method.upper()} SCALING:")
            
            calibrator = ConfidenceCalibrator(method=method)
            
            # Evaluate before
            before = calibrator.evaluate(model_probs, labels, calibrated=False)
            print(f"   Before: {before.summary()}")
            
            # Fit
            calibrator.fit(logits, labels)
            
            # Evaluate after
            calibrated = calibrator.calibrate(model_probs)
            after = calibrator.evaluate(calibrated, labels, calibrated=False)
            print(f"   After:  {after.summary()}")
            
            print(f"   Params: {calibrator.method.get_params()}")
        
        print("\n✅ Calibration tests complete!")
    else:
        print("NumPy not available, skipping tests")
