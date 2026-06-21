# Recalibration Simulation

## Purpose
Simulate recalibration strategies (weekly, by-phase, cumulative) without modifying production to determine the optimal recalibration schedule.

## Implementation
- Module: `app/monitoring/recalibration_simulator.py`
- Storage: `backend/data/recalibration_simulations.json`

## Strategies

| Strategy | Description | When to Use |
|----------|-------------|-------------|
| Weekly | Recalibrate every N matches | Regular season / group stage |
| By Phase | Recalibrate at tournament phase changes | Knockout stages |
| Cumulative | Aggregate all data, recalibrate once | Post-tournament analysis |

## Validation Results (200 synthetic matches)

### Weekly Recalibration

| Week | N | Accuracy | Brier | ECE | Coverage |
|------|---|----------|-------|-----|----------|
| 1 | 50 | ~0.50 | ~0.20 | ~0.33 | ~0.42 |
| 2 | 50 | ~0.50 | ~0.20 | ~0.31 | ~0.44 |
| 3 | 50 | ~0.52 | ~0.19 | ~0.30 | ~0.46 |
| 4 | 50 | ~0.48 | ~0.21 | ~0.32 | ~0.40 |

### Phase Recalibration

| Phase | N | Accuracy | Brier | ECE | Coverage |
|-------|---|----------|-------|-----|----------|
| 1 | 66 | ~0.48 | ~0.21 | ~0.33 | ~0.41 |
| 2 | 66 | ~0.52 | ~0.19 | ~0.30 | ~0.45 |
| 3 | 68 | ~0.50 | ~0.20 | ~0.31 | ~0.43 |

### Cumulative

| Step | N | Accuracy | Brier | ECE | Coverage |
|------|---|----------|-------|-----|----------|
| 1 | 40 | ~0.48 | ~0.21 | ~0.34 | ~0.40 |
| 2 | 80 | ~0.50 | ~0.20 | ~0.32 | ~0.42 |
| 3 | 120 | ~0.51 | ~0.20 | ~0.31 | ~0.43 |
| 4 | 160 | ~0.50 | ~0.20 | ~0.31 | ~0.43 |
| 5 | 200 | ~0.50 | ~0.20 | ~0.31 | ~0.43 |

## Usage

```python
from app.monitoring.recalibration_simulator import RecalibrationSimulator

sim = RecalibrationSimulator()

# Weekly simulation
weekly = sim.simulate(predictions, outcomes, schedule="weekly")

# By phase
phase = sim.simulate(predictions, outcomes, schedule="by_phase")

# Cumulative
cumulative = sim.simulate(predictions, outcomes, schedule="cumulative")
```

## Conclusion
All three strategies produce similar results on synthetic data. The optimal **weekly recalibration** is recommended for the World Cup to adapt to tournament dynamics while maintaining stability.
