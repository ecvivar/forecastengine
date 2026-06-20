# Elo Sensitivity Decomposition

## Global Metrics
| Metric | Value |
|--------|-------|
| Global mean dP/dElo | 0.000307 |
| Global mean elasticity | 1.3156 |

## Sensitivity by Elo Range
| Range | Count | Mean dP/dElo | Mean Elasticity |
|-------|-------|-------------|----------------|
| <1500 | 0 | 0 | 0 |
| 1500-1650 | 19 | 0.000336 | 1.5352 |
| 1650-1800 | 79 | 0.000389 | 1.7318 |
| 1800-1950 | 49 | 0.000311 | 1.2535 |
| >1950 | 45 | 0.000145 | 0.5597 |

## Key Findings
1. Elo is the primary sensitivity driver (dP/dElo = 0.000307)
2. Elasticity = 1.3156 -- 1% Elo change -> ~131.56% probability change
3. Root cause of stress std = 0.09
4. Recommendation: reduce elo_weight or bound Elo changes
