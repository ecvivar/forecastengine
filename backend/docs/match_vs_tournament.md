# Match vs Tournament Consistency Report

## Correlation Analysis

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Teams analyzed | 47 | — | — |
| Pearson r (Match vs Overall) | 0.982515 | > 0.80 | PASS |
| Spearman r (Match vs Overall) | 0.982771 | > 0.80 | PASS |
| Pearson r (Attack vs Overall) | 0.841494 | — | — |
| Pearson r (Defense vs Overall) | 0.782352 | — | — |

## Interpretation

**Pearson r = 0.9825** — extremely strong correlation.
The match-level strength (average of attack and defense composites) and tournament-level
overall_strength are highly aligned because they share the same underlying signals.

The key difference: attack/defense include only xG and FIFA, while overall_strength
also includes Elo. Yet the correlation remains very high because xG and FIFA dominate

both measures.

## Team Strength Comparison

| Team | Overall | Match | Attack | Defense |
|------|---------|-------|--------|---------|
| Netherlands | 1.5166 | 1.6500 | 1.3666 | 1.9333 |
| Colombia | 1.4224 | 1.5220 | 1.3250 | 1.7190 |
| Germany | 1.3900 | 1.3792 | 1.3250 | 1.4333 |
| France | 1.3797 | 1.4643 | 1.3777 | 1.5510 |
| Belgium | 1.3391 | 1.4443 | 1.0917 | 1.7970 |
| England | 1.2779 | 1.2979 | 1.2250 | 1.3708 |
| Brazil | 1.2493 | 1.2012 | 1.1191 | 1.2833 |
| Argentina | 1.2427 | 1.2105 | 1.1305 | 1.2905 |
| Spain | 1.2332 | 1.1775 | 1.2341 | 1.1209 |
| Chile | 1.2100 | 1.2542 | 1.0750 | 1.4333 |

## Conclusion: PASS

- Pearson r = 0.9825 >> 0.80 target
- Match and tournament engines use coherent signals
- No refactoring of overall_strength needed
- The architectural separation (Poisson xG for matches, composite for tournaments) is validated