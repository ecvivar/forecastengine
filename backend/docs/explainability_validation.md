# Explainability Validation Report

## Validation Results

| Metric | Value |
|--------|-------|
| Matches validated | 100 |
| Max driver sum error | 0.0 |
| Mean driver sum error | 0.0 |
| Passing (<1% error) | 100.0% |
| FIFA non-zero matches | 100.0% |

## Average Driver Contributions

| Driver | Average % |
|--------|----------|
| elo | 31.14% |
| xg_attack | 27.50% |
| xg_defense | 25.32% |
| home_advantage | 9.37% |
| fifa | 4.11% |
| dixon_coles | 2.57% |
| **Sum** | 100.01% |

## Sample Match Explanations


### Canada vs Morocco
- Home win prob: 0.4923
- Driver sum: 1.0000
  - xg_defense: 44.17%
  - xg_attack: 26.29%
  - elo: 12.35%
  - home_advantage: 7.36%
  - fifa: 5.85%
  - dixon_coles: 3.99%

### Honduras vs Switzerland
- Home win prob: 0.2593
- Driver sum: 1.0000
  - xg_attack: 64.39%
  - xg_defense: 14.34%
  - fifa: 6.73%
  - home_advantage: 5.91%
  - elo: 4.60%
  - dixon_coles: 4.02%

### Spain vs Netherlands
- Home win prob: 0.6165
- Driver sum: 1.0000
  - xg_defense: 73.09%
  - home_advantage: 11.10%
  - elo: 9.83%
  - xg_attack: 3.54%
  - fifa: 1.66%
  - dixon_coles: 0.79%

### Portugal vs Spain
- Home win prob: 0.3950
- Driver sum: 1.0000
  - elo: 48.24%
  - home_advantage: 20.20%
  - xg_defense: 12.16%
  - xg_attack: 8.53%
  - fifa: 6.76%
  - dixon_coles: 4.12%

### Brazil vs Netherlands
- Home win prob: 0.5729
- Driver sum: 1.0000
  - xg_defense: 53.11%
  - xg_attack: 19.34%
  - elo: 14.18%
  - home_advantage: 10.71%
  - fifa: 1.99%
  - dixon_coles: 0.68%

## Key Findings

1. **100% of matches pass** the <1% sum error criterion
2. **FIFA is now non-zero in 100%** of matches (was 0% in Sprint 3)
3. **Drivers sum to 100%** with machine precision (0.000000 mean error)
4. **Elo is the largest driver** (31.14%) — correct for a model where Elo flows through Bayesian prior AND attack/defense
5. **FIFA average 4.11%** is within the 1-10% target
6. **Distribution is realistic**: xG attack (27.5%) + xG defense (25.3%) = 52.8% total xG > Elo (31.1%)