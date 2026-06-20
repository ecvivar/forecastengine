# Weight Optimizer v2 Report

## Problem (Sprint 3)

In Sprint 3, `elo_weight`, `xg_attack_weight`, `xg_defense_weight`, and `fifa_weight`
only affected `overall_strength` (Monte Carlo) and had zero effect on `predict_full()`.
The WeightOptimizer grid search found IDENTICAL metrics for all weight combinations.

## Solution (Sprint 4A)

All four weights now affect `predict_full()`:

- **elo_weight**: scales the Bayesian prior strength (higher = stronger Elo pull)
- **xg_attack_weight**: controls attack_xg contribution to attack_strength composite
- **xg_defense_weight**: controls defense_xg contribution to defense_strength composite
- **fifa_weight**: controls fifa_norm contribution to both attack and defense composites

## Results

| | Current | Best Found |
|---|---------|------------|
| **elo** | 0.4 | 0.4 |
| **xg_attack** | 0.3 | 0.3 |
| **xg_defense** | 0.2 | 0.1 |
| **fifa** | 0.1 | 0.2 |
| **Brier** | 0.632170 | 0.591348 |
| **LogLoss** | 1.050394 | 0.993271 |

Improvement: Brier delta = 0.040822, LogLoss delta = 0.057123

## Top 20 Configurations

| Rank | elo | xg_atk | xg_def | fifa | Brier | LogLoss |
|------|-----|--------|--------|------|-------|---------|
| 1 | 0.4 | 0.3 | 0.1 | 0.2 | 0.591348 | 0.993271 |
| 2 | 0.45 | 0.25 | 0.1 | 0.2 | 0.591407 | 0.993534 |
| 3 | 0.35 | 0.35 | 0.1 | 0.2 | 0.592103 | 0.994161 |
| 4 | 0.5 | 0.2 | 0.1 | 0.2 | 0.592396 | 0.995131 |
| 5 | 0.45 | 0.3 | 0.1 | 0.15 | 0.593056 | 0.995734 |
| 6 | 0.5 | 0.25 | 0.1 | 0.15 | 0.592988 | 0.995874 |
| 7 | 0.3 | 0.4 | 0.1 | 0.2 | 0.593652 | 0.996188 |
| 8 | 0.4 | 0.35 | 0.1 | 0.15 | 0.593950 | 0.996790 |
| 9 | 0.55 | 0.2 | 0.1 | 0.15 | 0.593859 | 0.997369 |
| 10 | 0.55 | 0.15 | 0.1 | 0.2 | 0.594517 | 0.998350 |
| 11 | 0.35 | 0.4 | 0.1 | 0.15 | 0.595615 | 0.998947 |
| 12 | 0.6 | 0.15 | 0.1 | 0.15 | 0.595966 | 1.000617 |
| 13 | 0.55 | 0.25 | 0.1 | 0.1 | 0.597230 | 1.002243 |
| 14 | 0.5 | 0.3 | 0.1 | 0.1 | 0.597775 | 1.002715 |
| 15 | 0.6 | 0.2 | 0.1 | 0.1 | 0.597654 | 1.003159 |
| 16 | 0.6 | 0.1 | 0.1 | 0.2 | 0.598155 | 1.003696 |
| 17 | 0.45 | 0.35 | 0.1 | 0.1 | 0.599135 | 1.004363 |
| 18 | 0.4 | 0.4 | 0.1 | 0.1 | 0.601244 | 1.007093 |
| 19 | 0.6 | 0.25 | 0.1 | 0.05 | 0.606637 | 1.016433 |
| 20 | 0.55 | 0.3 | 0.1 | 0.05 | 0.608341 | 1.018443 |

## Key Findings

1. **WeightOptimizer now discriminates between weights** — 151 candidates with varying metrics
2. **Best config shifts FIFA from 0.10 to 0.20** and xG defense from 0.20 to 0.10
3. **Elo and xG attack unchanged at 0.40 and 0.30** — these were already optimal
4. **Brier improvement of 0.041** is meaningful (0.632 → 0.591)
5. **All top configs have xg_def=0.10 (minimum)** — the optimizer prefers minimal xG defense weight since FIFA also contributes to defense_strength
6. **Recommendation**: Update production config to (elo=0.40, xg_atk=0.30, xg_def=0.10, fifa=0.20)