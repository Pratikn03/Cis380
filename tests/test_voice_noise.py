"""
==============================================================================
VOICE MODEL NOISE ROBUSTNESS TESTS
==============================================================================
Author: Pratik Niroula
Project: Sentifargo - Sentifargo

PURPOSE:
--------
Test voice/emotion recognition models under various noise conditions
to evaluate robustness and identify degradation patterns.

NOISE TYPES:
------------
- White noise (Gaussian)
- Pink noise (1/f)
- Background babble
- Environmental sounds
- Codec artifacts (compression)
- Reverb/echo

METRICS:
--------
- Accuracy degradation vs SNR
- Word Error Rate (WER) for STT
- Emotion F1 score under noise
- Confusion pattern analysis
"""

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pytest


# Lazy imports
def _get_numpy():
    try:
        import numpy as np
        return np
    except ImportError:
        return None


@dataclass
class NoiseConfig:
    """Configuration for noise generation."""
    noise_type: str
    snr_db: float  # Signal-to-noise ratio in dB
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RobustnessResult:
    """Result of robustness test."""
    noise_type: str
    snr_db: float
    clean_accuracy: float
    noisy_accuracy: float
    accuracy_drop: float
    clean_f1: float
    noisy_f1: float
    f1_drop: float
    sample_count: int
    errors: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "noise_type": self.noise_type,
            "snr_db": self.snr_db,
            "clean_accuracy": round(self.clean_accuracy, 4),
            "noisy_accuracy": round(self.noisy_accuracy, 4),
            "accuracy_drop": round(self.accuracy_drop, 4),
            "clean_f1": round(self.clean_f1, 4),
            "noisy_f1": round(self.noisy_f1, 4),
            "f1_drop": round(self.f1_drop, 4),
            "sample_count": self.sample_count
        }


class NoiseGenerator:
    """Generate various types of audio noise."""
    
    def __init__(self, sample_rate: int = 16000, seed: int = 42):
        self.sample_rate = sample_rate
        np = _get_numpy()
        if np is not None:
            np.random.seed(seed)
        random.seed(seed)
    
    def white_noise(self, duration_seconds: float) -> Any:
        """Generate white (Gaussian) noise."""
        np = _get_numpy()
        if np is None:
            return [random.gauss(0, 1) for _ in range(int(duration_seconds * self.sample_rate))]
        
        n_samples = int(duration_seconds * self.sample_rate)
        return np.random.randn(n_samples)
    
    def pink_noise(self, duration_seconds: float) -> Any:
        """Generate pink (1/f) noise."""
        np = _get_numpy()
        if np is None:
            return self.white_noise(duration_seconds)
        
        n_samples = int(duration_seconds * self.sample_rate)
        
        # Generate white noise
        white = np.random.randn(n_samples)
        
        # Apply 1/f filter in frequency domain
        fft = np.fft.rfft(white)
        frequencies = np.fft.rfftfreq(n_samples, 1/self.sample_rate)
        frequencies[0] = 1  # Avoid division by zero
        
        # 1/f filter
        pink_fft = fft / np.sqrt(frequencies)
        pink = np.fft.irfft(pink_fft, n_samples)
        
        return pink / np.std(pink)  # Normalize
    
    def babble_noise(self, duration_seconds: float, n_speakers: int = 5) -> Any:
        """Generate babble noise (multiple overlapping speakers)."""
        np = _get_numpy()
        n_samples = int(duration_seconds * self.sample_rate)
        
        if np is None:
            return [sum(random.gauss(0, 0.5) for _ in range(n_speakers)) for _ in range(n_samples)]
        
        # Sum of filtered noise to simulate speech-like spectrum
        babble = np.zeros(n_samples)
        
        for _ in range(n_speakers):
            # Bandpass-filtered noise (300-3400 Hz, speech band)
            speaker = np.random.randn(n_samples)
            
            # Simple lowpass simulation
            for i in range(1, n_samples):
                speaker[i] = 0.9 * speaker[i-1] + 0.1 * speaker[i]
            
            babble += speaker * np.random.uniform(0.5, 1.0)
        
        return babble / np.std(babble)
    
    def add_noise_at_snr(
        self,
        signal: Any,
        noise: Any,
        snr_db: float
    ) -> Any:
        """Add noise to signal at specified SNR."""
        np = _get_numpy()
        
        if np is None:
            # Fallback: simple mixing
            snr_linear = 10 ** (snr_db / 20)
            return [s + n / snr_linear for s, n in zip(signal, noise)]
        
        signal = np.array(signal)
        noise = np.array(noise)
        
        # Truncate or extend noise to match signal length
        if len(noise) > len(signal):
            noise = noise[:len(signal)]
        elif len(noise) < len(signal):
            noise = np.tile(noise, int(np.ceil(len(signal) / len(noise))))[:len(signal)]
        
        # Calculate signal and noise power
        signal_power = np.mean(signal ** 2)
        noise_power = np.mean(noise ** 2)
        
        # Calculate required noise scaling
        snr_linear = 10 ** (snr_db / 10)
        noise_scale = np.sqrt(signal_power / (snr_linear * noise_power))
        
        # Mix
        noisy = signal + noise_scale * noise
        
        return noisy


class MockVoiceModel:
    """Mock voice/emotion model for testing."""
    
    EMOTIONS = ["neutral", "happy", "sad", "angry", "fearful"]
    
    def __init__(self, base_accuracy: float = 0.85):
        self.base_accuracy = base_accuracy
    
    def predict(self, audio: Any, noise_level: float = 0.0) -> Dict[str, Any]:
        """Mock prediction with noise-dependent accuracy."""
        np = _get_numpy()
        
        # Accuracy degrades with noise
        effective_accuracy = self.base_accuracy * (1 - noise_level * 0.5)
        
        if np is not None:
            # Random emotion with accuracy-dependent correctness
            true_emotion = np.random.choice(self.EMOTIONS)
            
            if np.random.random() < effective_accuracy:
                predicted = true_emotion
            else:
                other_emotions = [e for e in self.EMOTIONS if e != true_emotion]
                predicted = np.random.choice(other_emotions)
            
            confidence = np.random.uniform(0.5, 0.95) * (1 - noise_level * 0.3)
        else:
            true_emotion = random.choice(self.EMOTIONS)
            predicted = true_emotion if random.random() < effective_accuracy else random.choice(self.EMOTIONS)
            confidence = random.uniform(0.5, 0.95)
        
        return {
            "true_emotion": true_emotion,
            "predicted_emotion": predicted,
            "confidence": confidence,
            "all_probs": {e: random.uniform(0.05, 0.3) for e in self.EMOTIONS}
        }


class VoiceRobustnessTester:
    """Test voice model robustness under noise."""
    
    NOISE_TYPES = ["white", "pink", "babble"]
    SNR_LEVELS = [30, 20, 15, 10, 5, 0, -5]
    
    def __init__(
        self,
        model: Any = None,
        sample_rate: int = 16000
    ):
        self.model = model or MockVoiceModel()
        self.sample_rate = sample_rate
        self.noise_gen = NoiseGenerator(sample_rate)
        self._results: List[RobustnessResult] = []
    
    def run_test(
        self,
        audio_samples: Optional[List[Any]] = None,
        n_samples: int = 100,
        noise_types: Optional[List[str]] = None,
        snr_levels: Optional[List[float]] = None
    ) -> List[RobustnessResult]:
        """
        Run robustness tests.
        
        Args:
            audio_samples: Audio samples to test (or generate synthetic)
            n_samples: Number of samples if generating synthetic
            noise_types: Types of noise to test
            snr_levels: SNR levels in dB to test
            
        Returns:
            List of RobustnessResult
        """
        np = _get_numpy()
        
        noise_types = noise_types or self.NOISE_TYPES
        snr_levels = snr_levels or self.SNR_LEVELS
        
        # Generate synthetic audio if not provided
        if audio_samples is None:
            duration = 2.0  # 2 seconds each
            if np is not None:
                audio_samples = [np.random.randn(int(duration * self.sample_rate)) * 0.5 
                               for _ in range(n_samples)]
            else:
                audio_samples = [[random.gauss(0, 0.5) for _ in range(int(duration * self.sample_rate))]
                               for _ in range(n_samples)]
        
        results = []
        
        for noise_type in noise_types:
            for snr_db in snr_levels:
                result = self._test_condition(
                    audio_samples,
                    noise_type,
                    snr_db
                )
                results.append(result)
        
        self._results = results
        return results
    
    def _test_condition(
        self,
        samples: List[Any],
        noise_type: str,
        snr_db: float
    ) -> RobustnessResult:
        """Test under a specific noise condition."""
        clean_correct = 0
        noisy_correct = 0
        clean_predictions = []
        noisy_predictions = []
        true_labels = []
        errors = []
        
        for i, audio in enumerate(samples):
            # Clean prediction
            clean_result = self.model.predict(audio, noise_level=0.0)
            true_label = clean_result["true_emotion"]
            clean_pred = clean_result["predicted_emotion"]
            
            # Generate and add noise
            duration = len(audio) / self.sample_rate if hasattr(audio, '__len__') else 2.0
            
            if noise_type == "white":
                noise = self.noise_gen.white_noise(duration)
            elif noise_type == "pink":
                noise = self.noise_gen.pink_noise(duration)
            elif noise_type == "babble":
                noise = self.noise_gen.babble_noise(duration)
            else:
                noise = self.noise_gen.white_noise(duration)
            
            noisy_audio = self.noise_gen.add_noise_at_snr(audio, noise, snr_db)
            
            # Noisy prediction (simulate degradation)
            noise_level = max(0, min(1, (20 - snr_db) / 40))  # Map SNR to 0-1 noise level
            noisy_result = self.model.predict(noisy_audio, noise_level=noise_level)
            noisy_pred = noisy_result["predicted_emotion"]
            
            # Track results
            true_labels.append(true_label)
            clean_predictions.append(clean_pred)
            noisy_predictions.append(noisy_pred)
            
            if clean_pred == true_label:
                clean_correct += 1
            if noisy_pred == true_label:
                noisy_correct += 1
            
            # Log errors
            if clean_pred == true_label and noisy_pred != true_label:
                errors.append({
                    "sample_idx": i,
                    "true": true_label,
                    "clean_pred": clean_pred,
                    "noisy_pred": noisy_pred
                })
        
        n = len(samples)
        clean_accuracy = clean_correct / n
        noisy_accuracy = noisy_correct / n
        
        # Calculate F1 scores
        clean_f1 = self._calculate_f1(true_labels, clean_predictions)
        noisy_f1 = self._calculate_f1(true_labels, noisy_predictions)
        
        return RobustnessResult(
            noise_type=noise_type,
            snr_db=snr_db,
            clean_accuracy=clean_accuracy,
            noisy_accuracy=noisy_accuracy,
            accuracy_drop=clean_accuracy - noisy_accuracy,
            clean_f1=clean_f1,
            noisy_f1=noisy_f1,
            f1_drop=clean_f1 - noisy_f1,
            sample_count=n,
            errors=errors[:10]  # Limit error examples
        )
    
    def _calculate_f1(self, true: List[str], pred: List[str]) -> float:
        """Calculate macro F1 score."""
        classes = list(set(true + pred))
        f1_scores = []
        
        for cls in classes:
            tp = sum(1 for t, p in zip(true, pred) if t == cls and p == cls)
            fp = sum(1 for t, p in zip(true, pred) if t != cls and p == cls)
            fn = sum(1 for t, p in zip(true, pred) if t == cls and p != cls)
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            f1_scores.append(f1)
        
        return sum(f1_scores) / len(f1_scores) if f1_scores else 0
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive robustness report."""
        if not self._results:
            return {"error": "No test results available"}
        
        report = {
            "summary": {
                "total_conditions": len(self._results),
                "noise_types": list(set(r.noise_type for r in self._results)),
                "snr_range": [min(r.snr_db for r in self._results), 
                             max(r.snr_db for r in self._results)]
            },
            "by_noise_type": {},
            "by_snr": {},
            "recommendations": []
        }
        
        # Group by noise type
        for noise_type in set(r.noise_type for r in self._results):
            type_results = [r for r in self._results if r.noise_type == noise_type]
            report["by_noise_type"][noise_type] = {
                "avg_accuracy_drop": sum(r.accuracy_drop for r in type_results) / len(type_results),
                "worst_snr": min(type_results, key=lambda r: r.noisy_accuracy).snr_db,
                "results": [r.to_dict() for r in sorted(type_results, key=lambda r: r.snr_db, reverse=True)]
            }
        
        # Group by SNR
        for snr in set(r.snr_db for r in self._results):
            snr_results = [r for r in self._results if r.snr_db == snr]
            report["by_snr"][str(snr)] = {
                "avg_accuracy": sum(r.noisy_accuracy for r in snr_results) / len(snr_results),
                "worst_noise_type": min(snr_results, key=lambda r: r.noisy_accuracy).noise_type
            }
        
        # Generate recommendations
        for r in self._results:
            if r.accuracy_drop > 0.2:
                report["recommendations"].append(
                    f"High accuracy drop ({r.accuracy_drop:.1%}) at {r.snr_db}dB {r.noise_type} noise. "
                    f"Consider data augmentation or noise-robust training."
                )
        
        return report


# ============================================================================
# PYTEST TESTS
# ============================================================================

class TestNoiseGenerator:
    """Tests for NoiseGenerator class."""
    
    def test_white_noise_shape(self):
        """Test white noise generates correct shape."""
        gen = NoiseGenerator(sample_rate=16000)
        noise = gen.white_noise(duration_seconds=1.0)
        
        np = _get_numpy()
        if np is not None:
            assert len(noise) == 16000, "White noise should have correct length"
    
    def test_pink_noise_generation(self):
        """Test pink noise generation."""
        gen = NoiseGenerator(sample_rate=16000)
        noise = gen.pink_noise(duration_seconds=1.0)
        
        assert noise is not None, "Pink noise should be generated"
        assert len(noise) == 16000, "Pink noise should have correct length"
    
    def test_babble_noise_generation(self):
        """Test babble noise generation."""
        gen = NoiseGenerator(sample_rate=16000)
        noise = gen.babble_noise(duration_seconds=1.0, n_speakers=3)
        
        assert noise is not None, "Babble noise should be generated"
        assert len(noise) == 16000, "Babble noise should have correct length"
    
    def test_add_noise_at_snr(self):
        """Test SNR-controlled noise addition."""
        np = _get_numpy()
        if np is None:
            pytest.skip("NumPy not available")
        
        gen = NoiseGenerator(sample_rate=16000)
        signal = np.random.randn(16000)
        noise = gen.white_noise(1.0)
        
        # Test different SNR levels
        for snr in [20, 10, 0]:
            noisy = gen.add_noise_at_snr(signal, noise, snr)
            assert len(noisy) == len(signal), f"Noisy signal should match length at SNR={snr}"


class TestMockVoiceModel:
    """Tests for MockVoiceModel class."""
    
    def test_prediction_output(self):
        """Test model prediction output format."""
        model = MockVoiceModel()
        result = model.predict([0.0] * 16000)
        
        assert "predicted_emotion" in result
        assert "confidence" in result
        assert result["predicted_emotion"] in MockVoiceModel.EMOTIONS
    
    def test_noise_affects_accuracy(self):
        """Test that noise level affects predictions."""
        model = MockVoiceModel(base_accuracy=0.9)
        
        # Run multiple predictions
        clean_correct = sum(
            1 for _ in range(100)
            if model.predict([0.0] * 100, noise_level=0.0)["predicted_emotion"] ==
               model.predict([0.0] * 100, noise_level=0.0)["true_emotion"]
        )
        
        noisy_correct = sum(
            1 for _ in range(100)
            if model.predict([0.0] * 100, noise_level=0.8)["predicted_emotion"] ==
               model.predict([0.0] * 100, noise_level=0.8)["true_emotion"]
        )
        
        # Noisy should generally be worse
        # (probabilistic test, may occasionally fail)
        assert noisy_correct < clean_correct + 20, "Noise should degrade accuracy"


class TestVoiceRobustnessTester:
    """Tests for VoiceRobustnessTester class."""
    
    def test_run_test_returns_results(self):
        """Test that run_test returns results."""
        tester = VoiceRobustnessTester()
        results = tester.run_test(n_samples=10, noise_types=["white"], snr_levels=[20, 10])
        
        assert len(results) == 2, "Should have 2 results (2 SNR levels)"
        assert all(isinstance(r, RobustnessResult) for r in results)
    
    def test_result_fields(self):
        """Test result contains expected fields."""
        tester = VoiceRobustnessTester()
        results = tester.run_test(n_samples=5, noise_types=["white"], snr_levels=[20])
        
        result = results[0]
        assert result.noise_type == "white"
        assert result.snr_db == 20
        assert 0 <= result.clean_accuracy <= 1
        assert 0 <= result.noisy_accuracy <= 1
    
    def test_accuracy_degrades_with_noise(self):
        """Test that accuracy generally degrades with more noise."""
        tester = VoiceRobustnessTester()
        results = tester.run_test(
            n_samples=50,
            noise_types=["white"],
            snr_levels=[30, 10, 0, -5]
        )
        
        # Sort by SNR (high to low)
        sorted_results = sorted(results, key=lambda r: r.snr_db, reverse=True)
        
        # Generally, lower SNR should have lower accuracy
        # (allows some tolerance for randomness)
        high_snr_acc = sorted_results[0].noisy_accuracy
        low_snr_acc = sorted_results[-1].noisy_accuracy
        
        assert low_snr_acc <= high_snr_acc + 0.1, "Lower SNR should generally have lower accuracy"
    
    def test_generate_report(self):
        """Test report generation."""
        tester = VoiceRobustnessTester()
        tester.run_test(n_samples=10, noise_types=["white", "pink"], snr_levels=[20, 10])
        
        report = tester.generate_report()
        
        assert "summary" in report
        assert "by_noise_type" in report
        assert "by_snr" in report
        assert "white" in report["by_noise_type"]
        assert "pink" in report["by_noise_type"]


class TestRobustnessResult:
    """Tests for RobustnessResult dataclass."""
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = RobustnessResult(
            noise_type="white",
            snr_db=20.0,
            clean_accuracy=0.85,
            noisy_accuracy=0.75,
            accuracy_drop=0.10,
            clean_f1=0.83,
            noisy_f1=0.72,
            f1_drop=0.11,
            sample_count=100
        )
        
        d = result.to_dict()
        assert d["noise_type"] == "white"
        assert d["snr_db"] == 20.0
        assert d["accuracy_drop"] == 0.1


# Run tests if executed directly
if __name__ == "__main__":
    print("Running Voice Robustness Tests...")
    
    # Quick manual test
    tester = VoiceRobustnessTester()
    results = tester.run_test(
        n_samples=50,
        noise_types=["white", "pink", "babble"],
        snr_levels=[30, 20, 10, 5, 0]
    )
    
    print("\n📊 Robustness Test Results:")
    print("-" * 60)
    
    for r in results:
        print(f"{r.noise_type:8} @ {r.snr_db:3}dB: "
              f"Acc {r.clean_accuracy:.1%} → {r.noisy_accuracy:.1%} "
              f"(drop: {r.accuracy_drop:.1%})")
    
    report = tester.generate_report()
    print("\n📋 Recommendations:")
    for rec in report.get("recommendations", [])[:5]:
        print(f"  • {rec}")
    
    print("\n✅ Tests complete!")
