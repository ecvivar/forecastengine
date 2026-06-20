# Backtesting Report

## Methodology

Monte Carlo tournament simulation (500 sims) for each World Cup using teams built from historical match data (Elo, xG proxy from average goals).

## Results

| Tournament | Predicted Champion | Actual Champion | Champion Prob% | Top4 Acc | Finalist Acc | Brier | Log Loss |
|-----------|-------------------|----------------|---------------|---------|-------------|------|---------|
| 2014 | Brazil | Germany | 17.0% | 0.25 | 0.00 | 0.6945 | 1.1398 |
| 2018 | Argentina | France | 13.6% | 0.25 | 0.00 | 0.6322 | 1.0378 |
| 2022 | France | France | 14.8% | 0.50 | 0.50 | 0.6537 | 1.0978 |

## Analysis

1. **2022 correctly predicted France as champion** (14.8% probability).
2. **2014 predicted Brazil** (17.0%) — actual champion Germany was a realistic contender.
3. **2018 predicted Argentina** (13.6%) — actual champion France was underrated.
4. **Top 4 accuracy (25-50%)** reflects the high uncertainty of tournament prediction.
5. **Limitation**: Historical data lacks real xG metrics. xG_for/xG_against are approximated from actual goals, which inflates calibration metrics.
