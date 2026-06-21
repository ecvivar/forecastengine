# Prediction Drift Detection

## Purpose
Detect distributional shifts in Elo ratings, predictions, and uncertainty metrics during the World Cup.

## Implementation
- Module: `app/monitoring/drift_detector.py`

## Metrics

| Metric | Description | Interpretation | Threshold |
|--------|-------------|----------------|-----------|
| PSI (Population Stability Index) | Binned distribution comparison | > 0.10 = significant drift | 0.10 |
| KL Divergence | Relative entropy between distributions | > 0.10 = distribution change | 0.10 |
| JS Divergence | Jensen-Shannon Divergence (symmetric) | > 0.05 = material shift | 0.05 |

## Monitored Distributions

| Distribution | What it tracks | Why it matters |
|-------------|----------------|----------------|
| Elo | Team strength distribution | Tournament dynamics / format changes |
| Prediction | Probability distribution | Model bias shifts |
| Uncertainty | CI width / spread distribution | Model confidence changes |

## Validation Results

| Distribution | PSI | KL | JS | Drift? |
|-------------|-----|----|----|--------|
| Elo | < 0.10 | < 0.10 | < 0.05 | No |
| Prediction | < 0.10 | < 0.10 | < 0.05 | No |
| Uncertainty | < 0.10 | < 0.10 | < 0.05 | No |

> Note: Current results use synthetic data with mild drift. Real World Cup data will trigger actual alerts when distributions shift.

## Usage

```python
from app.monitoring.drift_detector import DriftDetector
import numpy as np

detector = DriftDetector()

# Full check
result = detector.full_check(
    current_elos=np.array([...]),
    reference_elos=np.array([...]),
    current_preds=np.array([...]),
    reference_preds=np.array([...]),
    current_uncertainty=np.array([...]),
    reference_uncertainty=np.array([...]),
)

if result["any_drift"]:
    for dist, report in result.items():
        if isinstance(report, dict) and report.get("drift_detected"):
            print(f"ALERT: {dist} drifted - {report['alerts']}")
```

## Alerting Strategy
- **WARNING**: Any single metric exceeds threshold
- **CRITICAL**: Two or more distributions show drift
- **ACTION**: Trigger recalibration and notify operators
