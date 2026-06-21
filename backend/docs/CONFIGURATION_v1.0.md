# ForecastEngine2026 v1.0 — Configuration Snapshot

## PredictionConfig (Production Values)

| Parameter | Value | Description |
|-----------|-------|-------------|
| elo_weight | 0.40 | Elo rating contribution to strength |
| xg_attack_weight | 0.30 | xG attack strength contribution |
| xg_defense_weight | 0.20 | xG defense strength contribution |
| fifa_weight | 0.10 | FIFA ranking contribution |
| home_advantage | 0.08 | Home field goal boost |
| dixon_coles_tau | 0.10 | Low-score correlation correction |
| bayesian_prior_strength | 0.50 | Bayesian update intensity |
| max_goals | 10 | Max goals considered in score probs |
| league_avg_goals | 1.25 | Baseline league average goals |
| top_n_scores | 10 | Top scorelines returned |
| elo_compression_scale | 0 | Elo compression (0 = disabled) |

## Effective Weights (After Normalization)

| Signal | Normalized Weight |
|--------|-------------------|
| Elo | 0.40 / 1.00 = **40%** |
| xG Attack | 0.30 / 1.00 = **30%** |
| xG Defense | 0.20 / 1.00 = **20%** |
| FIFA | 0.10 / 1.00 = **10%** |

## Bayesian Prior

| Parameter | Value |
|-----------|-------|
| base_prior_strength | 0.50 |
| elo_scale_factor | elo_weight / 0.40 |
| effective_prior | 0.50 × (0.40 / 0.40) = 0.50 |

The Bayesian prior shrinks predictions toward 50/50 by `prior_strength`.
Higher elo_weight increases the prior strength proportionally.

## Temperature Scaling

| Parameter | Value |
|-----------|-------|
| Optimal T | ~0.94 |
| Type | Global (single parameter) |
| Regional variants | 5 regions (independent T per continent) |

## Regional Calibration Regions

| Region | Teams |
|--------|-------|
| South America | CONMEBOL members |
| Europe | UEFA members |
| Africa | CAF members |
| Asia | AFC members |
| North America | CONCACAF members |

## Ensemble Weights (Optimized)

| Model | Weight |
|-------|--------|
| Poisson-xG | 0.25 |
| Bayesian Elo | 0.25 |
| Dixon-Coles | 0.25 |
| Strength Diff | 0.25 |

(Default equal weights; optimized via WeightOptimizer)

## Monte Carlo Configuration

| Parameter | Value |
|-----------|-------|
| num_simulations | 100,000 (default) |
| parallel | True (4 workers) |
| use_numba | True |
| Groups | 12 (groups A-L, 4 teams each) |
| Knockout | R32 → R16 → QF → SF → Final |
| Third-placed qualifiers | Best 8 of 12 |

## Bootstrap Settings

| Parameter | Value |
|-----------|-------|
| n_resamples | 1000 |
| CI level | 90% |
| Method | Percentile bootstrap |

## Uncertainty Formula

```
Uncertainty = 0.20 × RD + 0.50 × ensemble_disagreement + 0.30 × bootstrap_variance
```

Where:
- RD = rating_deviation (Glicko-style)
- ensemble_disagreement = std of 4 model predictions
- bootstrap_variance = variance of bootstrap resamples

## Drift Detection Thresholds

| Metric | Threshold |
|--------|-----------|
| PSI | 0.10 |
| KL Divergence | 0.10 |
| JS Divergence | 0.05 |

## Calibration Alarm Thresholds

| Metric | Warning Level |
|--------|---------------|
| ECE | > 0.045 |
| Brier | > 0.22 |

## Simulation Config (Default)

| Parameter | Value |
|-----------|-------|
| num_simulations | 100,000 |
| parallel | True |
| random_seed | None |

All configuration is frozen as of **ForecastEngine2026 v1.0**.
