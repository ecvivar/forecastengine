# Tournament Monitoring Dashboard Data

## Purpose
Expose structured JSON for frontend consumption with real-time tournament status and metrics.

## Implementation
- Module: `app/monitoring/dashboard_metrics.py`
- Output: `backend/data/dashboard_metrics.json`

## Endpoints (JSON Format)

### Top Contenders
```json
{
  "top_contenders": [
    {"team": "Brazil", "elo": 1578.0},
    {"team": "France", "elo": 1533.0},
    {"team": "Argentina", "elo": 1492.0}
  ]
}
```

### Champion Probabilities
```json
{
  "champion_probabilities": [
    {"team": "Brazil", "prob": 0.22},
    {"team": "France", "prob": 0.18},
    {"team": "Argentina", "prob": 0.14}
  ]
}
```

### Biggest Movers
```json
{
  "biggest_movers": [
    {"team": "Brazil", "elo_change": 10.5}
  ]
}
```

### Most Uncertain / Most Stable Teams
```json
{
  "most_uncertain_teams": [
    {"team": "Portugal", "uncertainty": 0.30}
  ],
  "most_stable_teams": [
    {"team": "Brazil", "stability": 0.88}
  ]
}
```

### Calibration Status
```json
{
  "calibration_status": {
    "accuracy": 0.50,
    "brier": 0.20,
    "ece": 0.30,
    "drift_warning": false
  }
}
```

## Usage

```python
from app.monitoring.dashboard_metrics import DashboardMetrics

dm = DashboardMetrics()
data = dm.compute(
    teams=team_list,
    elos=elo_dict,
    champion_probs=prob_dict,
    prediction_history=history,
    uncertainty_scores=uncertainty_dict,
)
# data is also saved to backend/data/dashboard_metrics.json
```

## Consumption
The dashboard JSON is designed for frontend polling. It includes all necessary fields for:
- Leaderboard display
- Champion probability bars
- Team movement tracking
- Uncertainty visualization
- Calibration health status
