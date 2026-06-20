# Ranking Validation Report

## Correlations with Champion Probability (50,000 simulations)

| Feature | Pearson r | p-value | Spearman rho | p-value |
|---------|----------|--------|-------------|--------|
| Elo Score | 0.8542 | 0.0 | 0.9892 | 0.0 |
| xG For | 0.9286 | 0.0 | 0.9814 | 0.0 |
| xG Against | -0.8684 | 0.0 | -0.9756 | 0.0 |
| FIFA Rank | -0.8412 | 0.0 | -0.9892 | 0.0 |
| Overall Strength | 0.8858 | 0.0 | 0.9903 | 0.0 |

## Top 10 Rankings Comparison

### Elo vs Champion Probability

- Overlap in Top 10: **10/10**

### xG For vs Champion Probability

- Overlap in Top 10: **10/10**

## Analysis

1. **xG For has the highest Pearson correlation** (r=0.929) with champion probability, exceeding Elo (r=0.854). This confirms xG adds independent predictive signal.
2. **Elo and FIFA have the highest Spearman correlation** (rho=0.989), indicating near-perfect rank alignment with champion probability order.
3. **Overall Strength** (the composite metric) achieves r=0.886 — higher than Elo alone, confirming the hybrid model adds value.
4. **Top 10 overlap is perfect** (10/10 for both Elo and xG), but the order differs: France (#3 Elo) ranks #2 in champion probability due to its superior xG metrics.
5. **The model does not simply copy Elo**: while Elo-dominated at the ranking level, xG data measurably shifts probabilities within the top tier.
