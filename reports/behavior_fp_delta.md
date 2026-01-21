# Behavior False-Positive Comparison

## Autoencoder

| Metric | Baseline | Augmented | Delta |
| --- | --- | --- | --- |
| FPR | 0.0374 | 0.0355 | -0.0019 |

Baseline confusion: {"tn": 3010, "fp": 117, "fn": 539, "tp": 70}

Augmented confusion: {"tn": 3016, "fp": 111, "fn": 673, "tp": 84}

## LOF

| Metric | Baseline | Augmented | Delta |
| --- | --- | --- | --- |
| FPR | 0.0448 | 0.0422 | -0.0026 |

Baseline confusion: {"tn": 2987, "fp": 140, "fn": 562, "tp": 47}

Augmented confusion: {"tn": 2995, "fp": 132, "fn": 694, "tp": 63}
