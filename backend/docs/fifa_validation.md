# FIFA Influence Validation Report

## Sprint 4A Changes

The `fifa_norm` range was tightened from [0.3, 3.0] to [0.7, 1.3] and FIFA was
integrated into `attack_strength` and `defense_strength` via weighted composite formulas:

```
attack_strength = (xg_attack_weight * attack_xg + fifa_weight * fifa_norm)
                 / (xg_attack_weight + fifa_weight)
defense_strength = (xg_defense_weight * defense_xg + fifa_weight * fifa_norm)
                  / (xg_defense_weight + fifa_weight)
```

## Scenario Results

| Scenario | Home Win | FIFA Driver % | Delta pp |
|----------|---------|--------------|---------|
| Equal FIFA (both rank 50) | 0.4427 | 13.26% | 0.8100 |
| Big FIFA gap (10 vs 150) | 0.5142 | 4.15% | 1.1300 |
| Same Elo/xG, FIFA gap only (5 vs 100) | 0.4337 | 1.55% | 0.0900 |
| Strong team good FIFA vs weak team bad FIFA | 0.5310 | 2.87% | 1.0400 |
| FIFA offsetting weak xG | 0.4213 | 2.08% | 0.5700 |

## Historical Match Summary (192 matches)

| Metric | Value |
|--------|-------|
| min_pct | 0.81 |
| p25_pct | 2.44 |
| mean_pct | 4.15 |
| median_pct | 3.44 |
| p75_pct | 4.85 |
| max_pct | 18.16 |

**Mean FIFA influence: 4.15% (well within 1-10% target)**

## Validation

- FIFA driver is non-zero in 100% of historical matches
- Mean influence (4.15%) is within the 1-10% target
- Absolute delta in home_win_prob is small but real (0.01-1.13 pp)
- The 18.16% max occurs when teams have equal Elo/xG but different FIFA (edge case)
- WeightOptimizer now produces different metrics for different weight combos