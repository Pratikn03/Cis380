# MLOps Roadmap: Shadow Mode & Model Updates

## Overview

This document outlines the MLOps roadmap for UAIS-v2, including shadow mode deployment, model validation, and safe rollout strategies.

## Current MLOps Stack

| Component | Status | Technology |
|-----------|--------|------------|
| Model Registry | ✅ Implemented | `src/mlops/registry.py` + MLflow |
| Experiment Tracking | ✅ Implemented | MLflow |
| Data Versioning | ✅ Implemented | DVC |
| Confidence Scoring | ✅ Implemented | `src/mlops/confidence.py` |
| A/B Testing | ✅ Implemented | `src/mlops/ab_testing.py` |
| Latency Monitoring | ✅ Implemented | `app/monitoring/latency.py` |
| Audit Logging | ✅ Implemented | `src/mlops/audit_logger.py` |

## Shadow Mode Architecture

### What is Shadow Mode?

Shadow mode runs a new model version in parallel with production, comparing predictions without affecting users. This enables:

1. **Safe validation** - Test new models on real traffic
2. **Performance comparison** - Compare latency, accuracy, drift
3. **Gradual rollout** - Increase traffic percentage over time
4. **Instant rollback** - Switch back without deployment

### Implementation Plan

#### Phase 1: Shadow Infrastructure (Q2 2024)

```
┌─────────────────────────────────────────────────────────┐
│                     Request                              │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                  Traffic Router                          │
│  ┌───────────────┐     ┌───────────────────────────┐   │
│  │ Production    │     │ Shadow (async)             │   │
│  │ Model v1.2    │     │ Model v1.3-candidate       │   │
│  │ (100% serve)  │     │ (100% mirror, 0% serve)    │   │
│  └───────┬───────┘     └───────────────┬───────────┘   │
│          │                             │                │
│          ▼                             ▼                │
│    User Response              Shadow Metrics            │
│                               (logged only)             │
└─────────────────────────────────────────────────────────┘
```

**Files to create:**
- `src/mlops/shadow_mode.py` - Shadow routing logic
- `src/mlops/shadow_metrics.py` - Comparison metrics
- `app/api/routes/shadow.py` - Shadow management API

#### Phase 2: Comparison Dashboard (Q2 2024)

Compare shadow vs production on:
- Prediction distribution differences
- Latency percentiles (p50, p95, p99)
- Confidence score calibration
- Feature importance shifts
- Error rate by input type

**Files to create:**
- `dashboard/components/shadow_comparison.py` - Streamlit component
- `reports/shadow/` - Generated comparison reports

#### Phase 3: Automated Promotion (Q3 2024)

Automated promotion criteria:
```python
PROMOTION_CRITERIA = {
    "min_shadow_duration_hours": 168,  # 1 week
    "min_request_count": 10000,
    "max_prediction_drift": 0.05,  # KL divergence
    "max_latency_increase_pct": 10,
    "min_confidence_correlation": 0.95,
    "max_error_rate_increase": 0.01,
}
```

### Shadow Mode Implementation

```python
# src/mlops/shadow_mode.py (planned)

from dataclasses import dataclass
from typing import Dict, Any, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)

@dataclass
class ShadowConfig:
    """Shadow mode configuration"""
    enabled: bool = False
    shadow_model_id: str = ""
    shadow_percentage: float = 100.0  # % of requests to shadow
    log_predictions: bool = True
    compare_async: bool = True

class ShadowRouter:
    """Routes requests to production and shadow models"""
    
    def __init__(self, config: ShadowConfig):
        self.config = config
        self.production_model = None
        self.shadow_model = None
        
    async def predict(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Get production prediction, optionally run shadow"""
        # Always get production prediction
        production_result = await self.production_model.predict(request)
        
        # Run shadow in background (async)
        if self.config.enabled and self._should_shadow():
            asyncio.create_task(
                self._run_shadow_comparison(request, production_result)
            )
        
        return production_result
    
    async def _run_shadow_comparison(
        self, 
        request: Dict[str, Any],
        production_result: Dict[str, Any]
    ) -> None:
        """Run shadow model and log comparison"""
        try:
            shadow_result = await self.shadow_model.predict(request)
            
            # Log comparison metrics
            self._log_comparison(
                request=request,
                production=production_result,
                shadow=shadow_result
            )
        except Exception as e:
            logger.error(f"Shadow prediction failed: {e}")
```

## Canary Deployment

After shadow validation, use canary deployment:

```
Phase 1: 1% traffic  → 24 hours → check metrics
Phase 2: 5% traffic  → 24 hours → check metrics
Phase 3: 25% traffic → 48 hours → check metrics
Phase 4: 50% traffic → 48 hours → check metrics
Phase 5: 100% traffic → promoted
```

Automatic rollback triggers:
- Error rate increase > 5%
- Latency p99 increase > 20%
- Prediction drift detected
- Manual intervention

## Rollback Procedures

### Immediate Rollback

```bash
# Using the model registry
python -m src.mlops.registry rollback --model fraud_detector --to-version v1.2

# Using the A/B testing framework
python -m src.mlops.ab_testing set-traffic --model fraud_detector --version v1.2 --percentage 100
```

### API Endpoint (planned)

```
POST /api/v1/models/{model_name}/rollback
{
    "target_version": "v1.2",
    "reason": "Latency regression detected"
}
```

## Monitoring During Rollout

### Key Metrics

| Metric | Alert Threshold | Rollback Threshold |
|--------|-----------------|-------------------|
| Error rate | > 1% | > 5% |
| Latency p99 | > 500ms | > 1000ms |
| Prediction drift | > 0.03 | > 0.1 |
| OOM events | > 0 | > 1 |
| Confidence calibration | < 0.9 | < 0.8 |

### Alerts

Configured in `app/monitoring/alerts.py`:
- Slack notifications for warnings
- PagerDuty for critical alerts
- Automated rollback for threshold breaches

## Timeline

| Phase | Target | Status |
|-------|--------|--------|
| Shadow Infrastructure | Q2 2024 | 🔲 Planned |
| Comparison Dashboard | Q2 2024 | 🔲 Planned |
| Automated Promotion | Q3 2024 | 🔲 Planned |
| Canary Deployment | Q3 2024 | 🔲 Planned |
| Full Automation | Q4 2024 | 🔲 Planned |

## Related Documentation

- [Model Registry](../src/mlops/README.md)
- [A/B Testing Framework](../src/mlops/ab_testing.py)
- [Confidence Scoring](../src/mlops/confidence.py)
- [Latency Monitoring](../app/monitoring/latency.py)
