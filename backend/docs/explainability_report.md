# Explainability Report

## Match Explainability (FASE 5)

### Brazil vs Argentina (Strong Pair)

| Driver | Value |
|--------|-------|
| xg_attack | 0.3606 (36.1%) |
| elo | 0.2854 (28.5%) |
| home_advantage | 0.2516 (25.2%) |
| xg_defense | 0.0977 (9.8%) |
| dixon_coles | 0.0047 (0.5%) |
| fifa | 0.0000 (0.0%) |

**Interpretation:** xG Attack dominates (36.1%) because both teams have high Elo (close together), but Brazil's xG_for (2.3) exceeds Argentina's (2.1). Home advantage contributes 25.2%. FIFA has 0% impact on match-level prediction.

### Drivers Sum Check

**Sum of drivers:** 1.0000 = 100.0% — passes sum-to-100% check.

## Tournament Explainability (FASE 7)

### Average Signal Contribution Across 32 Teams (2022)

| Signal | Average Contribution |
|--------|---------------------|
| elo | 39.8% |
| xg | 41.5% |
| fifa | 18.7% |
| other | 0.0% |
| **Sum** | **100.0%** |

### Top 3 Teams

| Team | Strength | Elo% | xG% | FIFA% |
|------|---------|------|-----|-------|
| England | 1.7150 | 30.3% | 52.2% | 17.5% |
| Brazil | 1.7067 | 34.4% | 48.0% | 17.6% |
| Spain | 1.6700 | 31.1% | 50.9% | 18.0% |

## API Endpoint (FASE 6)

`GET /api/v1/matches/explain?home_team_id=...&away_team_id=...`

Returns prediction + per-signal driver breakdown. All values come from real ablation computations — no hardcoded percentages.

## Validation

- All drivers are computed from actual engine deltas, not hardcoded.
- Match-level drivers sum to ~100% after normalization.
- Tournament-level drivers (elo + xg + fifa) sum to 100% by construction from overall_strength formula.
- FIFA shows 0% in match explainability (it only affects Monte Carlo overall_strength).
