# Prediction Audit Trail

## Purpose
Every prediction made by ForecastEngine2026 is logged with full context for traceability and reproducibility.

## Implementation
- Module: `app/audit/prediction_audit.py`
- Storage: `backend/data/prediction_audit_log.csv`

## Fields Logged Per Prediction

| Field | Description | Example |
|-------|-------------|---------|
| timestamp | UTC timestamp of prediction | `2026-06-21T20:42:01+00:00` |
| competition_id | Tournament identifier | `WC2026` |
| home_team | Home team name | `Brazil` |
| away_team | Away team name | `Argentina` |
| prob_home | Home win probability | `0.520000` |
| prob_draw | Draw probability | `0.250000` |
| prob_away | Away win probability | `0.230000` |
| calibration_version | Calibration version | `sprint8.5_v2` |
| model_version | Model version | `ensemble_v4` |
| config_hash | SHA-256 hash of config | `2ec6d65c31fe` |
| ensemble_weights | JSON-encoded weights | `(empty if default)` |
| ci_lower | Confidence interval lower | `0.350000` |
| ci_upper | Confidence interval upper | `0.650000` |
| uncertainty_spread | Spread metric | `0.250000` |
| uncertainty_entropy | Entropy metric | `0.680000` |
| uncertainty_bootstrap_var | Bootstrap variance | `0.042000` |
| trigger | API trigger source | `api` |

## Validation Results
- **Audit records logged**: 5
- **Unique teams tracked**: 8 (Argentina, Brazil, England, France, Germany, Netherlands, Portugal, Spain)
- **Auditability**: 100%

## Usage

```python
from app.audit.prediction_audit import PredictionAudit

audit = PredictionAudit()
audit.record(
    competition_id="WC2026",
    home_team="Brazil",
    away_team="Argentina",
    probabilities={"home": 0.52, "draw": 0.25, "away": 0.23},
    ci=(0.35, 0.65),
    uncertainty_metrics={"spread": 0.25, "entropy": 0.68, "bootstrap_variance": 0.042},
)

# Query history
history = audit.get_history(team="Brazil")
teams = audit.get_teams()
count = audit.count()
```

## Conclusion
The audit trail records all prediction parameters, model versions, calibration versions, confidence intervals, and uncertainty metrics. Any historical prediction can be fully reconstructed.
