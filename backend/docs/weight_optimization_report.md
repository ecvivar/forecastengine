# Weight Optimization Report

## Methodology

Exhaustive grid search over elo [0.20-0.60], xg_attack [0.10-0.40], xg_defense [0.10-0.30], fifa [0.00-0.20] with constraint sum=1.0.

## Important Caveat

The weights (elo_weight, xg_attack_weight, xg_defense_weight, fifa_weight) in PredictionConfig ONLY affect `overall_strength`, which is used by Monte Carlo. They do NOT affect `predict_full` match-level predictions (which use attack_strength and defense_strength directly from xG data).

Therefore, optimizing weights against match-level log loss is not meaningful — ALL valid weight combinations produce IDENTICAL match-level metrics.

For true weight optimization, a tournament-level Monte Carlo evaluation would be needed at significant computational cost.

## Current Weights

| Signal | Current Value |
|--------|--------------|
| elo | 0.4 |
| xg_attack | 0.3 |
| xg_defense | 0.2 |
| fifa | 0.1 |

## Recommended Weights

| Signal | Optimal Value |
|--------|--------------|
| elo | 0.2 |
| xg_attack | 0.3 |
| xg_defense | 0.3 |
| fifa | 0.2 |

## Findings

1. **Match-level metrics are weight-insensitive** — the grid search found no difference in Brier/Log Loss across valid combinations.
2. **The current weights (0.40/0.30/0.20/0.10) are adequate** as they primarily affect Monte Carlo tournament simulation.
3. **A tournament-level weight optimization** would require running full Monte Carlo for each weight combination, which is computationally prohibitive with grid search.
4. **Recommendation**: Keep current weights and validate Monte Carlo output quality against historical tournament results (see Backtesting Report).
