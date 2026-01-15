"""
Cross-Modal Synthetic Data Generator for Fusion Model Training

Generates realistic cross-modal anomaly scenarios combining:
- Fraud signals (transaction patterns)
- Cyber signals (network intrusion indicators)
- Behavior signals (user activity patterns)
- Voice signals (emotional/stress indicators)
- Vision signals (facial/body language cues)

These synthetic examples enable training the fusion model on correlated
multi-modal anomalies that would be rare in production data.
"""

import json
import random
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ModalitySignal:
    """Base signal from a single modality"""
    modality: str
    confidence: float
    anomaly_score: float
    features: Dict[str, Any]
    timestamp: str


@dataclass
class CrossModalSample:
    """A cross-modal training sample with correlated signals"""
    sample_id: str
    scenario_type: str
    ground_truth_label: str  # "anomaly" or "normal"
    ground_truth_severity: float  # 0.0-1.0
    signals: List[ModalitySignal]
    correlation_strength: float  # How correlated the signals are
    description: str
    created_at: str


class CrossModalScenario:
    """Base class for cross-modal anomaly scenarios"""
    
    def __init__(self, scenario_type: str):
        self.scenario_type = scenario_type
        
    def generate_signals(self, is_anomaly: bool) -> Tuple[List[ModalitySignal], float, str]:
        """Generate correlated signals for this scenario
        
        Returns:
            signals: List of ModalitySignal objects
            severity: Ground truth severity (0-1)
            description: Human-readable description
        """
        raise NotImplementedError


class InsiderThreatScenario(CrossModalScenario):
    """
    Insider threat scenario correlating:
    - Behavior: Unusual access patterns, off-hours activity
    - Cyber: Data exfiltration attempts, privilege escalation
    - Voice (optional): Stress indicators in recorded calls
    """
    
    def __init__(self):
        super().__init__("insider_threat")
        
    def generate_signals(self, is_anomaly: bool) -> Tuple[List[ModalitySignal], float, str]:
        signals = []
        timestamp = datetime.now().isoformat()
        
        if is_anomaly:
            # Generate correlated anomaly signals
            base_anomaly = random.uniform(0.6, 0.95)
            def noise() -> float:
                return random.uniform(-0.1, 0.1)
            
            # Behavior signal - unusual patterns
            signals.append(ModalitySignal(
                modality="behavior",
                confidence=0.85 + noise() * 0.1,
                anomaly_score=base_anomaly + noise(),
                features={
                    "off_hours_access_ratio": random.uniform(0.4, 0.8),
                    "sensitive_file_access_count": random.randint(50, 200),
                    "unusual_resource_pattern": True,
                    "session_duration_anomaly": random.uniform(2.0, 5.0),
                    "peer_group_deviation": random.uniform(0.6, 0.9)
                },
                timestamp=timestamp
            ))
            
            # Cyber signal - data exfiltration indicators
            signals.append(ModalitySignal(
                modality="cyber",
                confidence=0.8 + noise() * 0.1,
                anomaly_score=base_anomaly + noise(),
                features={
                    "data_volume_uploaded_mb": random.uniform(500, 5000),
                    "external_destination_count": random.randint(3, 15),
                    "encrypted_traffic_ratio": random.uniform(0.7, 0.95),
                    "protocol_anomaly_score": random.uniform(0.5, 0.9),
                    "time_since_last_similar": random.randint(30, 365)
                },
                timestamp=timestamp
            ))
            
            # Voice signal (if available) - stress indicators
            if random.random() > 0.3:  # 70% have voice data
                signals.append(ModalitySignal(
                    modality="voice",
                    confidence=0.7 + noise() * 0.15,
                    anomaly_score=base_anomaly * 0.8 + noise(),  # Voice slightly lower
                    features={
                        "stress_level": random.uniform(0.6, 0.9),
                        "speech_rate_deviation": random.uniform(1.2, 1.8),
                        "pitch_variability": random.uniform(0.4, 0.7),
                        "hesitation_count": random.randint(10, 30),
                        "emotion_detected": random.choice(["anxious", "nervous", "evasive"])
                    },
                    timestamp=timestamp
                ))
            
            severity = base_anomaly
            description = f"Insider threat: User showing {int(base_anomaly*100)}% anomaly indicators across behavior and cyber modalities"
            
        else:
            # Generate normal signals
            base_normal = random.uniform(0.05, 0.25)
            def noise() -> float:
                return random.uniform(-0.05, 0.05)
            
            signals.append(ModalitySignal(
                modality="behavior",
                confidence=0.9 + noise(),
                anomaly_score=base_normal + noise(),
                features={
                    "off_hours_access_ratio": random.uniform(0.0, 0.15),
                    "sensitive_file_access_count": random.randint(0, 10),
                    "unusual_resource_pattern": False,
                    "session_duration_anomaly": random.uniform(0.8, 1.2),
                    "peer_group_deviation": random.uniform(0.0, 0.2)
                },
                timestamp=timestamp
            ))
            
            signals.append(ModalitySignal(
                modality="cyber",
                confidence=0.9 + noise(),
                anomaly_score=base_normal + noise(),
                features={
                    "data_volume_uploaded_mb": random.uniform(0, 50),
                    "external_destination_count": random.randint(0, 2),
                    "encrypted_traffic_ratio": random.uniform(0.1, 0.4),
                    "protocol_anomaly_score": random.uniform(0.0, 0.2),
                    "time_since_last_similar": random.randint(0, 7)
                },
                timestamp=timestamp
            ))
            
            severity = base_normal
            description = "Normal user activity within expected parameters"
            
        return signals, severity, description


class FraudCollisionScenario(CrossModalScenario):
    """
    Fraud + Vision scenario (e.g., ATM fraud with camera):
    - Fraud: Unusual transaction patterns
    - Vision: Face doesn't match account holder, suspicious behavior
    - Behavior: Account access from unusual location/device
    """
    
    def __init__(self):
        super().__init__("fraud_collision")
        
    def generate_signals(self, is_anomaly: bool) -> Tuple[List[ModalitySignal], float, str]:
        signals = []
        timestamp = datetime.now().isoformat()
        
        if is_anomaly:
            base_anomaly = random.uniform(0.65, 0.98)
            def noise() -> float:
                return random.uniform(-0.1, 0.1)
            
            # Fraud signal
            signals.append(ModalitySignal(
                modality="fraud",
                confidence=0.88 + noise() * 0.08,
                anomaly_score=base_anomaly + noise(),
                features={
                    "transaction_amount_zscore": random.uniform(2.5, 6.0),
                    "velocity_ratio": random.uniform(3.0, 10.0),
                    "merchant_category_anomaly": True,
                    "distance_from_home_km": random.uniform(500, 5000),
                    "time_since_last_transaction_min": random.randint(1, 30)
                },
                timestamp=timestamp
            ))
            
            # Vision signal - face mismatch
            signals.append(ModalitySignal(
                modality="vision",
                confidence=0.75 + noise() * 0.1,
                anomaly_score=base_anomaly + noise() * 0.8,
                features={
                    "face_match_score": random.uniform(0.1, 0.4),
                    "known_fraudster_match": random.random() > 0.7,
                    "suspicious_behavior_score": random.uniform(0.5, 0.9),
                    "disguise_detected": random.random() > 0.5,
                    "multiple_people_detected": random.random() > 0.6
                },
                timestamp=timestamp
            ))
            
            # Behavior signal
            signals.append(ModalitySignal(
                modality="behavior",
                confidence=0.82 + noise() * 0.1,
                anomaly_score=base_anomaly * 0.85 + noise(),
                features={
                    "new_device": True,
                    "unusual_location": True,
                    "typing_pattern_match": random.uniform(0.1, 0.4),
                    "session_behavior_anomaly": random.uniform(0.5, 0.9),
                    "failed_auth_attempts": random.randint(1, 5)
                },
                timestamp=timestamp
            ))
            
            severity = base_anomaly
            description = "Fraud collision: Transaction anomaly correlated with face mismatch and behavioral deviation"
            
        else:
            base_normal = random.uniform(0.05, 0.2)
            def noise() -> float:
                return random.uniform(-0.05, 0.05)
            
            signals.append(ModalitySignal(
                modality="fraud",
                confidence=0.92 + noise(),
                anomaly_score=base_normal + noise(),
                features={
                    "transaction_amount_zscore": random.uniform(-1.0, 1.0),
                    "velocity_ratio": random.uniform(0.5, 1.5),
                    "merchant_category_anomaly": False,
                    "distance_from_home_km": random.uniform(0, 50),
                    "time_since_last_transaction_min": random.randint(60, 1440)
                },
                timestamp=timestamp
            ))
            
            signals.append(ModalitySignal(
                modality="vision",
                confidence=0.95 + noise(),
                anomaly_score=base_normal + noise(),
                features={
                    "face_match_score": random.uniform(0.85, 0.99),
                    "known_fraudster_match": False,
                    "suspicious_behavior_score": random.uniform(0.0, 0.2),
                    "disguise_detected": False,
                    "multiple_people_detected": False
                },
                timestamp=timestamp
            ))
            
            signals.append(ModalitySignal(
                modality="behavior",
                confidence=0.93 + noise(),
                anomaly_score=base_normal + noise(),
                features={
                    "new_device": False,
                    "unusual_location": False,
                    "typing_pattern_match": random.uniform(0.8, 0.98),
                    "session_behavior_anomaly": random.uniform(0.0, 0.2),
                    "failed_auth_attempts": 0
                },
                timestamp=timestamp
            ))
            
            severity = base_normal
            description = "Normal transaction with verified identity and expected behavior"
            
        return signals, severity, description


class NetworkIntrusionScenario(CrossModalScenario):
    """
    Network intrusion with physical security correlation:
    - Cyber: Network intrusion signatures
    - Behavior: Anomalous system access patterns
    - Vision: Unauthorized physical access detected
    """
    
    def __init__(self):
        super().__init__("network_intrusion")
        
    def generate_signals(self, is_anomaly: bool) -> Tuple[List[ModalitySignal], float, str]:
        signals = []
        timestamp = datetime.now().isoformat()
        
        if is_anomaly:
            base_anomaly = random.uniform(0.7, 0.95)
            def noise() -> float:
                return random.uniform(-0.1, 0.1)
            
            # Cyber signal - intrusion indicators
            signals.append(ModalitySignal(
                modality="cyber",
                confidence=0.9 + noise() * 0.05,
                anomaly_score=base_anomaly + noise(),
                features={
                    "attack_type": random.choice(["lateral_movement", "privilege_escalation", "data_exfiltration"]),
                    "affected_hosts_count": random.randint(5, 50),
                    "malicious_payload_detected": True,
                    "c2_communication_score": random.uniform(0.6, 0.95),
                    "encryption_anomaly": random.uniform(0.5, 0.9)
                },
                timestamp=timestamp
            ))
            
            # Behavior signal - system access anomalies
            signals.append(ModalitySignal(
                modality="behavior",
                confidence=0.85 + noise() * 0.1,
                anomaly_score=base_anomaly * 0.9 + noise(),
                features={
                    "privilege_escalation_attempt": True,
                    "service_account_misuse": random.random() > 0.4,
                    "lateral_movement_score": random.uniform(0.5, 0.9),
                    "anomalous_process_chain": True,
                    "credential_dumping_indicators": random.random() > 0.5
                },
                timestamp=timestamp
            ))
            
            # Vision signal - physical security (if applicable)
            if random.random() > 0.5:
                signals.append(ModalitySignal(
                    modality="vision",
                    confidence=0.7 + noise() * 0.15,
                    anomaly_score=base_anomaly * 0.7 + noise(),
                    features={
                        "unauthorized_access_detected": True,
                        "tailgating_detected": random.random() > 0.6,
                        "suspicious_loitering": random.random() > 0.5,
                        "after_hours_presence": True,
                        "badge_anomaly": random.random() > 0.4
                    },
                    timestamp=timestamp
                ))
            
            severity = base_anomaly
            description = f"Network intrusion: {signals[0].features['attack_type']} detected with behavioral correlation"
            
        else:
            base_normal = random.uniform(0.05, 0.2)
            def noise() -> float:
                return random.uniform(-0.05, 0.05)
            
            signals.append(ModalitySignal(
                modality="cyber",
                confidence=0.92 + noise(),
                anomaly_score=base_normal + noise(),
                features={
                    "attack_type": None,
                    "affected_hosts_count": 0,
                    "malicious_payload_detected": False,
                    "c2_communication_score": random.uniform(0.0, 0.15),
                    "encryption_anomaly": random.uniform(0.0, 0.2)
                },
                timestamp=timestamp
            ))
            
            signals.append(ModalitySignal(
                modality="behavior",
                confidence=0.95 + noise(),
                anomaly_score=base_normal + noise(),
                features={
                    "privilege_escalation_attempt": False,
                    "service_account_misuse": False,
                    "lateral_movement_score": random.uniform(0.0, 0.15),
                    "anomalous_process_chain": False,
                    "credential_dumping_indicators": False
                },
                timestamp=timestamp
            ))
            
            severity = base_normal
            description = "Normal network activity with expected system behavior"
            
        return signals, severity, description


class VoicePhishingScenario(CrossModalScenario):
    """
    Voice phishing (vishing) with multi-modal detection:
    - Voice: Stress, deception indicators
    - Fraud: Unusual transaction request patterns
    - Behavior: Call pattern anomalies
    """
    
    def __init__(self):
        super().__init__("voice_phishing")
        
    def generate_signals(self, is_anomaly: bool) -> Tuple[List[ModalitySignal], float, str]:
        signals = []
        timestamp = datetime.now().isoformat()
        
        if is_anomaly:
            base_anomaly = random.uniform(0.6, 0.92)
            def noise() -> float:
                return random.uniform(-0.1, 0.1)
            
            # Voice signal - caller deception indicators
            signals.append(ModalitySignal(
                modality="voice",
                confidence=0.78 + noise() * 0.12,
                anomaly_score=base_anomaly + noise(),
                features={
                    "caller_stress_level": random.uniform(0.3, 0.6),  # Phishers often calm
                    "scripted_speech_score": random.uniform(0.6, 0.9),
                    "urgency_language_detected": True,
                    "authority_impersonation_score": random.uniform(0.5, 0.9),
                    "known_phishing_phrase_match": random.uniform(0.4, 0.8),
                    "voiceprint_known_fraudster": random.random() > 0.6
                },
                timestamp=timestamp
            ))
            
            # Fraud signal - transaction anomaly
            signals.append(ModalitySignal(
                modality="fraud",
                confidence=0.82 + noise() * 0.1,
                anomaly_score=base_anomaly * 0.85 + noise(),
                features={
                    "request_type": random.choice(["wire_transfer", "password_reset", "account_update"]),
                    "request_amount": random.uniform(1000, 50000) if random.random() > 0.3 else None,
                    "urgency_score": random.uniform(0.7, 1.0),
                    "beneficiary_risk_score": random.uniform(0.5, 0.95),
                    "similar_recent_requests": random.randint(5, 50)
                },
                timestamp=timestamp
            ))
            
            # Behavior signal - call pattern
            signals.append(ModalitySignal(
                modality="behavior",
                confidence=0.75 + noise() * 0.15,
                anomaly_score=base_anomaly * 0.8 + noise(),
                features={
                    "caller_id_spoofed": random.random() > 0.3,
                    "call_duration_anomaly": random.uniform(0.4, 0.8),
                    "time_of_call_anomaly": random.uniform(0.3, 0.7),
                    "victim_profile_match": random.uniform(0.5, 0.9),
                    "previous_contact_exists": random.random() > 0.8
                },
                timestamp=timestamp
            ))
            
            severity = base_anomaly
            description = f"Voice phishing: {signals[1].features['request_type']} request with deception indicators"
            
        else:
            base_normal = random.uniform(0.05, 0.25)
            def noise() -> float:
                return random.uniform(-0.05, 0.05)
            
            signals.append(ModalitySignal(
                modality="voice",
                confidence=0.88 + noise(),
                anomaly_score=base_normal + noise(),
                features={
                    "caller_stress_level": random.uniform(0.1, 0.4),
                    "scripted_speech_score": random.uniform(0.1, 0.3),
                    "urgency_language_detected": False,
                    "authority_impersonation_score": random.uniform(0.0, 0.2),
                    "known_phishing_phrase_match": random.uniform(0.0, 0.1),
                    "voiceprint_known_fraudster": False
                },
                timestamp=timestamp
            ))
            
            signals.append(ModalitySignal(
                modality="fraud",
                confidence=0.92 + noise(),
                anomaly_score=base_normal + noise(),
                features={
                    "request_type": "inquiry",
                    "request_amount": None,
                    "urgency_score": random.uniform(0.0, 0.3),
                    "beneficiary_risk_score": random.uniform(0.0, 0.2),
                    "similar_recent_requests": random.randint(0, 2)
                },
                timestamp=timestamp
            ))
            
            signals.append(ModalitySignal(
                modality="behavior",
                confidence=0.9 + noise(),
                anomaly_score=base_normal + noise(),
                features={
                    "caller_id_spoofed": False,
                    "call_duration_anomaly": random.uniform(0.0, 0.2),
                    "time_of_call_anomaly": random.uniform(0.0, 0.2),
                    "victim_profile_match": random.uniform(0.0, 0.2),
                    "previous_contact_exists": True
                },
                timestamp=timestamp
            ))
            
            severity = base_normal
            description = "Normal customer service call with verified caller"
            
        return signals, severity, description


class CrossModalDataGenerator:
    """Generate cross-modal training data for fusion model"""
    
    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
            
        self.scenarios = [
            InsiderThreatScenario(),
            FraudCollisionScenario(),
            NetworkIntrusionScenario(),
            VoicePhishingScenario()
        ]
        
    def generate_sample(self, scenario: CrossModalScenario, is_anomaly: bool) -> CrossModalSample:
        """Generate a single cross-modal sample"""
        signals, severity, description = scenario.generate_signals(is_anomaly)
        
        # Calculate correlation strength (how consistent the signals are)
        if len(signals) > 1:
            scores = [s.anomaly_score for s in signals]
            correlation_strength = 1.0 - np.std(scores)  # Higher std = lower correlation
        else:
            correlation_strength = 1.0
            
        return CrossModalSample(
            sample_id=f"{scenario.scenario_type}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            scenario_type=scenario.scenario_type,
            ground_truth_label="anomaly" if is_anomaly else "normal",
            ground_truth_severity=severity,
            signals=signals,
            correlation_strength=correlation_strength,
            description=description,
            created_at=datetime.now().isoformat()
        )
    
    def generate_dataset(
        self,
        n_samples: int = 1000,
        anomaly_ratio: float = 0.3,
        scenario_weights: Optional[Dict[str, float]] = None
    ) -> List[CrossModalSample]:
        """Generate a balanced dataset of cross-modal samples
        
        Args:
            n_samples: Total number of samples to generate
            anomaly_ratio: Proportion of anomaly samples (0.0-1.0)
            scenario_weights: Optional weights for each scenario type
            
        Returns:
            List of CrossModalSample objects
        """
        if scenario_weights is None:
            scenario_weights = {s.scenario_type: 1.0 for s in self.scenarios}
            
        # Normalize weights
        total_weight = sum(scenario_weights.values())
        scenario_weights = {k: v/total_weight for k, v in scenario_weights.items()}
        
        samples = []
        n_anomalies = int(n_samples * anomaly_ratio)
        n_normal = n_samples - n_anomalies
        
        logger.info(f"Generating {n_samples} samples ({n_anomalies} anomalies, {n_normal} normal)")
        
        for is_anomaly, count in [(True, n_anomalies), (False, n_normal)]:
            for _ in range(count):
                # Select scenario based on weights
                scenario = random.choices(
                    self.scenarios,
                    weights=[scenario_weights.get(s.scenario_type, 0) for s in self.scenarios]
                )[0]
                
                samples.append(self.generate_sample(scenario, is_anomaly))
                
        # Shuffle the samples
        random.shuffle(samples)
        
        logger.info(f"Generated {len(samples)} cross-modal samples")
        return samples
    
    def export_to_json(self, samples: List[CrossModalSample], output_path: Path) -> None:
        """Export samples to JSON format"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert dataclass objects to dicts
        data = []
        for sample in samples:
            sample_dict = asdict(sample)
            # Ensure signals are properly serialized
            sample_dict["signals"] = [asdict(s) if hasattr(s, '__dataclass_fields__') else s 
                                      for s in sample.signals]
            data.append(sample_dict)
            
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
            
        logger.info(f"Exported {len(samples)} samples to {output_path}")
        
    def export_to_pytorch_format(self, samples: List[CrossModalSample], output_dir: Path) -> Dict[str, Any]:
        """Export samples in a format suitable for PyTorch DataLoader
        
        Creates:
        - features.npy: Numerical features matrix
        - labels.npy: Ground truth labels
        - metadata.json: Sample metadata
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Define feature dimensions per modality
        modality_dims = {
            "fraud": 10,
            "cyber": 10,
            "behavior": 10,
            "vision": 10,
            "voice": 10
        }
        total_dims = sum(modality_dims.values())
        
        features = np.zeros((len(samples), total_dims))
        labels = np.zeros(len(samples))
        severities = np.zeros(len(samples))
        metadata = []
        
        for i, sample in enumerate(samples):
            labels[i] = 1 if sample.ground_truth_label == "anomaly" else 0
            severities[i] = sample.ground_truth_severity
            
            # Extract features from each signal
            offset = 0
            for modality, dims in modality_dims.items():
                signal = next((s for s in sample.signals if s.modality == modality), None)
                if signal:
                    # Use anomaly_score and confidence as first two features
                    features[i, offset] = signal.anomaly_score
                    features[i, offset + 1] = signal.confidence
                    
                    # Extract numerical features from the signal
                    feat_values = []
                    for k, v in signal.features.items():
                        if isinstance(v, (int, float)):
                            feat_values.append(float(v))
                        elif isinstance(v, bool):
                            feat_values.append(1.0 if v else 0.0)
                            
                    # Fill remaining dimensions
                    for j, val in enumerate(feat_values[:dims-2]):
                        features[i, offset + 2 + j] = val
                        
                offset += dims
                
            metadata.append({
                "sample_id": sample.sample_id,
                "scenario_type": sample.scenario_type,
                "description": sample.description,
                "modalities_present": [s.modality for s in sample.signals]
            })
            
        # Save arrays
        np.save(output_dir / "features.npy", features)
        np.save(output_dir / "labels.npy", labels)
        np.save(output_dir / "severities.npy", severities)
        
        with open(output_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
            
        logger.info(f"Exported PyTorch format to {output_dir}")
        return {
            "n_samples": len(samples),
            "feature_dims": total_dims,
            "modality_dims": modality_dims,
            "anomaly_ratio": np.mean(labels)
        }


def main():
    """Generate synthetic cross-modal training data"""
    output_dir = Path(__file__).parent
    
    generator = CrossModalDataGenerator(seed=42)
    
    # Generate training set
    train_samples = generator.generate_dataset(
        n_samples=1000,
        anomaly_ratio=0.3
    )
    generator.export_to_json(train_samples, output_dir / "cross_modal_train.json")
    pytorch_info = generator.export_to_pytorch_format(train_samples, output_dir / "pytorch_train")
    
    # Generate validation set
    val_samples = generator.generate_dataset(
        n_samples=200,
        anomaly_ratio=0.3
    )
    generator.export_to_json(val_samples, output_dir / "cross_modal_val.json")
    generator.export_to_pytorch_format(val_samples, output_dir / "pytorch_val")
    
    # Generate test set
    test_samples = generator.generate_dataset(
        n_samples=200,
        anomaly_ratio=0.3
    )
    generator.export_to_json(test_samples, output_dir / "cross_modal_test.json")
    generator.export_to_pytorch_format(test_samples, output_dir / "pytorch_test")
    
    # Print summary
    print("\n" + "="*60)
    print("Cross-Modal Synthetic Data Generation Complete")
    print("="*60)
    print(f"\nTrain set: 1000 samples ({output_dir}/cross_modal_train.json)")
    print(f"Val set:   200 samples ({output_dir}/cross_modal_val.json)")
    print(f"Test set:  200 samples ({output_dir}/cross_modal_test.json)")
    print("\nPyTorch format:")
    print(f"  Feature dimensions: {pytorch_info['feature_dims']}")
    print(f"  Modality dimensions: {pytorch_info['modality_dims']}")
    print(f"  Anomaly ratio: {pytorch_info['anomaly_ratio']:.2%}")
    print("\nScenarios covered:")
    for scenario in generator.scenarios:
        print(f"  - {scenario.scenario_type}")


if __name__ == "__main__":
    main()
