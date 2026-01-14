# Sentifargo Benchmarks

End-to-end evaluation suite for the Sentifargo platform.

## Quick Start

```bash
# Run all benchmarks
python -m benchmarks.benchmark_suite

# Run with verbose output and save results
python -m benchmarks.benchmark_suite --verbose --save
```

## Benchmarks Included

| Benchmark | Description | Thresholds |
|-----------|-------------|------------|
| `intent_detection` | Orchestrator routing accuracy | accuracy ≥ 85%, confidence ≥ 70% |
| `fraud_detection` | Fraud model AUC/precision/recall | AUC ≥ 80%, P/R ≥ 70% |
| `rag_retrieval` | RAG retrieval quality (MRR, Recall@K) | MRR ≥ 60%, Recall@5 ≥ 70% |
| `latency` | System response latency | P50 ≤ 200ms, P95 ≤ 500ms |
| `multimodal_fusion` | Fusion model consistency | consistency ≥ 80% |

## Directory Structure

```
benchmarks/
├── benchmark_suite.py    # Main benchmark runner
├── datasets/             # Held-out test datasets
│   ├── intent_test.json
│   ├── fraud_test.csv
│   └── rag_test.json
├── results/              # Benchmark results (auto-generated)
│   └── Sentifargo_e2e_YYYYMMDD_HHMMSS.json
└── README.md
```

## Adding Custom Benchmarks

```python
from benchmarks.benchmark_suite import BaseBenchmark, BenchmarkResult

class MyBenchmark(BaseBenchmark):
    name = "my_benchmark"
    thresholds = {"accuracy": 0.90}
    
    def run(self) -> BenchmarkResult:
        # Your benchmark logic
        metrics = {"accuracy": 0.95}
        return BenchmarkResult(
            benchmark_name=self.name,
            timestamp=datetime.now().isoformat(),
            metrics=metrics,
            latency_ms=100.0,
            num_samples=100,
            passed=self._check_thresholds(metrics),
        )
```

## CI Integration

Add to `.github/workflows/ci.yml`:

```yaml
- name: Run Benchmarks
  run: |
    python -m benchmarks.benchmark_suite --save
```

## Results Format

```json
{
  "suite_name": "Sentifargo_e2e",
  "timestamp": "2026-01-08T12:00:00",
  "pass_rate": 1.0,
  "results": [
    {
      "benchmark_name": "intent_detection",
      "metrics": {"accuracy": 0.875, "avg_confidence": 0.82},
      "latency_ms": 150.5,
      "passed": true
    }
  ]
}
```
