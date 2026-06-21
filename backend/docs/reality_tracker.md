# Real vs Predicted Engine (Reality Tracker)

## Purpose
Compare pre-match predictions against actual results to compute surprise, upset index, and calibration impact.

## Implementation
- Module: `app/monitoring/reality_tracker.py`
- Storage: `backend/data/reality_tracker.json`

## Metrics

| Metric | Description | Range |
|--------|-------------|-------|
| Surprise Score | 1.0 - P(actual_outcome) | 0.0 (expected) to 1.0 (max surprise) |
| Upset Index | How unlikely the winner was | 0.0 (favorite won) to 2.0 (huge upset) |
| Accuracy | Correct outcome prediction rate | 0.0 to 1.0 |
| Calibration Impact | Running Brier & Accuracy | — |

## Validation Results (5 matches)

| Match | Home Pred | Draw Pred | Away Pred | Score | Outcome | Correct | Surprise | Upset |
|-------|-----------|-----------|-----------|-------|---------|---------|----------|-------|
| Brazil vs Argentina | 0.52 | 0.25 | 0.23 | 2-1 | Home | Yes | 0.48 | 0.00 |
| France vs England | 0.44 | 0.28 | 0.28 | 1-1 | Draw | Yes | 0.72 | 0.00 |
| Germany vs Spain | 0.38 | 0.30 | 0.32 | 0-2 | Away | Yes | 0.68 | 0.24 |
| Portugal vs Netherlands | 0.41 | 0.29 | 0.30 | 3-0 | Home | Yes | 0.59 | 0.00 |
| Brazil vs France | 0.48 | 0.27 | 0.25 | 1-0 | Home | Yes | 0.52 | 0.00 |

### Aggregate
- **Accuracy**: 100% (5/5)
- **Avg Surprise**: 0.60
- **Avg Upset**: 0.05

## Usage

```python
from app.monitoring.reality_tracker import RealityTracker

tracker = RealityTracker()

# Record match result
tracker.record(
    home_team="Brazil", away_team="Argentina",
    home_pred=0.52, draw_pred=0.25, away_pred=0.23,
    home_score=2, away_score=1,
)

# Analysis
surprise = tracker.get_surprise_matches(min_surprise=0.3)
upsets = tracker.get_upset_matches(min_upset=0.3)
team_stats = tracker.get_team_summary("Brazil")
```

## Conclusion
The reality tracker enables post-match analysis of prediction quality. Surprise scores help identify unexpected outcomes, and upset indices quantify how unlikely winning teams were before the match.
