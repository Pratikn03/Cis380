# Cross-Modal Synthetic Data for Fusion Model

## Overview

This directory contains synthetic data generation tools and datasets for training the multi-modal fusion model. Since real-world cross-modal anomaly data (where multiple modalities simultaneously exhibit correlated anomalies) is rare, we generate synthetic scenarios to train the fusion layer.

## Why Synthetic Data?

1. **Real Data Scarcity**: Cross-modal anomalies (e.g., fraud + face mismatch + behavioral deviation) are rare in production
2. **Label Quality**: Synthetic data has perfect ground truth labels
3. **Scenario Coverage**: Can generate edge cases that may not exist in historical data
4. **Privacy**: No PII concerns with synthetic data

## Scenarios Covered

### 1. Insider Threat
- **Modalities**: Behavior + Cyber + Voice (optional)
- **Pattern**: Employee data exfiltration
- **Signals**: Off-hours access, unusual file access, network exfiltration

### 2. Fraud Collision  
- **Modalities**: Fraud + Vision + Behavior
- **Pattern**: ATM/point-of-sale fraud with camera
- **Signals**: Transaction anomaly, face mismatch, behavioral deviation

### 3. Network Intrusion
- **Modalities**: Cyber + Behavior + Vision (optional)
- **Pattern**: APT with physical security correlation
- **Signals**: Intrusion signatures, access anomalies, unauthorized physical presence

### 4. Voice Phishing (Vishing)
- **Modalities**: Voice + Fraud + Behavior
- **Pattern**: Social engineering phone attacks
- **Signals**: Caller deception, transaction requests, call pattern anomalies

## Usage

### Generate Data

```bash
cd data/synthetic
python cross_modal_generator.py
```

This creates:
- `cross_modal_train.json` - 1000 training samples
- `cross_modal_val.json` - 200 validation samples  
- `cross_modal_test.json` - 200 test samples
- `pytorch_train/` - PyTorch-ready numpy arrays
- `pytorch_val/` - PyTorch-ready numpy arrays
- `pytorch_test/` - PyTorch-ready numpy arrays

### Custom Generation

```python
from cross_modal_generator import CrossModalDataGenerator

generator = CrossModalDataGenerator(seed=42)

# Generate with custom parameters
samples = generator.generate_dataset(
    n_samples=5000,
    anomaly_ratio=0.2,  # 20% anomalies
    scenario_weights={
        "insider_threat": 2.0,      # 2x weight
        "fraud_collision": 1.0,
        "network_intrusion": 1.5,
        "voice_phishing": 0.5       # 0.5x weight
    }
)

# Export
generator.export_to_json(samples, Path("my_dataset.json"))
generator.export_to_pytorch_format(samples, Path("my_pytorch_data"))
```

### Load in PyTorch

```python
import numpy as np
import torch
from torch.utils.data import TensorDataset, DataLoader

# Load data
features = np.load("pytorch_train/features.npy")
labels = np.load("pytorch_train/labels.npy")

# Create DataLoader
dataset = TensorDataset(
    torch.FloatTensor(features),
    torch.FloatTensor(labels)
)
loader = DataLoader(dataset, batch_size=32, shuffle=True)
```

## Data Schema

### JSON Format

```json
{
  "sample_id": "insider_threat_20240115120000123456",
  "scenario_type": "insider_threat",
  "ground_truth_label": "anomaly",
  "ground_truth_severity": 0.85,
  "correlation_strength": 0.92,
  "description": "Insider threat: User showing 85% anomaly indicators",
  "created_at": "2024-01-15T12:00:00.123456",
  "signals": [
    {
      "modality": "behavior",
      "confidence": 0.87,
      "anomaly_score": 0.83,
      "features": {
        "off_hours_access_ratio": 0.65,
        "sensitive_file_access_count": 127,
        "unusual_resource_pattern": true
      },
      "timestamp": "2024-01-15T12:00:00.123456"
    },
    {
      "modality": "cyber",
      "confidence": 0.82,
      "anomaly_score": 0.87,
      "features": {
        "data_volume_uploaded_mb": 2500,
        "external_destination_count": 8,
        "encrypted_traffic_ratio": 0.85
      },
      "timestamp": "2024-01-15T12:00:00.123456"
    }
  ]
}
```

### PyTorch Format

- `features.npy`: Shape `(n_samples, 50)` - 10 features per modality × 5 modalities
- `labels.npy`: Shape `(n_samples,)` - Binary labels (0=normal, 1=anomaly)
- `severities.npy`: Shape `(n_samples,)` - Continuous severity scores (0.0-1.0)
- `metadata.json`: Sample IDs and descriptions

## Integration with Fusion Model

The synthetic data is designed to work with `src/anomaly/fusion/model.py`:

```python
from src.anomaly.fusion.model import FusionModel
from data.synthetic.cross_modal_generator import CrossModalDataGenerator

# Generate data
generator = CrossModalDataGenerator()
train_samples = generator.generate_dataset(n_samples=5000)

# Train fusion model
model = FusionModel(config)
model.train(train_samples)
```

## Extending Scenarios

To add a new cross-modal scenario:

1. Create a new class inheriting from `CrossModalScenario`
2. Implement `generate_signals(is_anomaly)` method
3. Add to `self.scenarios` in `CrossModalDataGenerator.__init__`

```python
class NewScenario(CrossModalScenario):
    def __init__(self):
        super().__init__("new_scenario")
        
    def generate_signals(self, is_anomaly: bool):
        signals = []
        # Generate your modality signals here
        return signals, severity, description
```

## Validation

To validate synthetic data quality:

```bash
pytest tests/data/test_synthetic_data.py
```

Tests verify:
- Label distribution matches `anomaly_ratio`
- All scenarios are represented
- Feature values are within expected ranges
- Correlation strength is calculated correctly
