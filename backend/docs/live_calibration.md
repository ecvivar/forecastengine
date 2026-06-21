# Live Calibration Tracker

## Purpose
Continuously monitor calibration metrics during World Cup 2026 to detect degradation and drift in real-time.

## Implementation
- Module: `app/monitoring/calibration_tracker.py`
- Storage: `backend/data/calibration_tracker.json`

## Metrics Tracked

| Metric | Description | Target | Alarm Threshold |
|--------|-------------|--------|-----------------|
| Accuracy | Correct prediction rate | > 50% | < 45% |
| Brier Score | Mean squared error | < 0.22 | > 0.22 |
| LogLoss | Logarithmic loss | < 0.70 | > 0.70 |
| ECE | Expected Calibration Error | < 0.035 | > 0.045 |
| Coverage | 80% CI coverage rate | 88-92% | < 85% or > 95% |

## Aggregation Windows
- **Daily**: Per-day rolling metrics
- **Weekly**: 7-day rolling metrics
- **Tournament**: Tournament-wide cumulative metrics

## Validation Results

| Window | Entries | Accuracy | Brier | ECE | Coverage |
|--------|---------|----------|-------|-----|----------|
| Day 1-7 | 7 | ~0.50 | ~0.20 | ~0.30 | ~0.40 |

> Note: Training metrics use synthetic data; actual World Cup results will populate these automatically.

## Drift Warning Trigger
Drift warning activates when ECE > 0.045 or Brier > 0.22.

## Usage

```python
from app.monitoring.calibration_tracker import CalibrationTracker

tracker = CalibrationTracker()

# Record a batch of predictions
tracker.record_batch(predictions, outcomes, window="day")

# Get current status
status = tracker.get_status()
print(f"ECE: {status['ece']}, Drift: {status['drift_warning']}")

# Get tournament summary
summary = tracker.get_tournament_summary("world_cup_2026")
```

## Conclusion
The calibration tracker enables real-time monitoring of prediction quality during the World Cup. Any degradation in accuracy, calibration, or coverage is detected immediately with clear alarm thresholds.
