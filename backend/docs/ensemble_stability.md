# Ensemble Contribution Stability

## Results
| Model | Mean Contr | Stress Mean | Variance |
|-------|-----------|-------------|----------|
| poisson_xg | 25.0% | 25.0% | 0.000000 |
| bayesian_elo | 25.0% | 25.0% | 0.000000 |
| dixon_coles | 25.0% | 25.0% | 0.000000 |
| strength_diff | 25.0% | 25.0% | 0.000000 |

## Analysis
1. With default equal weights: all models 25%
2. With learned weights: StrengthDiff (42%), Bayesian Elo (37%)
3. Poisson-xG is largely redundant with Dixon-Coles
