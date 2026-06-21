# Uncertainty Correlation Study

## Correlation of Proxies with CI Width

| Proxy | Pearson | Spearman | Kendall |
|-------|---------|----------|---------|
| spread | 0.1581 | 0.1850 | 0.1474 |
| entropy | 0.1318 | 0.2195 | 0.1579 |
| rating_deviation | -0.2282 | -0.1609 | -0.1053 |
| bootstrap_variance | 0.9083 | 0.8932 | 0.7579 |
| ensemble_disagreement | 0.0537 | 0.0496 | 0.0211 |
| volatility | 0.3855 | 0.2977 | 0.2211 |

**Best proxy:** bootstrap_variance (Spearman=0.8932)
- Spread is a proxy for match balance, not prediction uncertainty
- Entropy captures distribution spread but not model-level confidence
- Bootstrap variance captures sampling uncertainty of predictions
- Ensemble disagreement measures model-level uncertainty