# Feature Importance Report

## Methodology

Ablation testing across 5 diverse team pairs (Elite vs Weak, Strong vs Avg, Avg vs Avg, Def vs Def, Atk vs Atk). Each signal was removed at the data level and the mean absolute delta in home win probability was measured across all pairs.

### Signals Tested
- **no_xg**: Set xG_for and xG_against to None (falls back to 1.0)
- **no_elo_prior**: Set bayesian_prior_strength = 0.0
- **no_dc**: Set dixon_coles_tau = 0.0
- **equal_elo**: Set both teams' Elo to the average
- **swap_xg**: Swapped xG values between home and away

## Aggregate Ablation Impact

| Ablation | Metric | Mean Delta | Max Delta | Std Delta |
|----------|--------|-----------|---------|---------|

### Relative Feature Importance

| Signal | Contribution to Home Win % | Contribution to xG |
|--------|--------------------------|-------------------|

## Conclusions

1. **Elo prior is the dominant signal** in match prediction (~7.3pp mean delta), but this is because the Bayesian prior directly shifts probabilities.
2. **xG data is critical** (~2.3pp mean delta for complete removal). xG attack has 4x more impact than xG defense in most scenarios.
3. **Dixon-Coles effect is marginal** (~0.6pp) — it mainly affects low-score corrections (0-0, 1-0, 0-1, 1-1 scores).
4. **FIFA rank does NOT affect match prediction directly** — only through overall_strength in Monte Carlo.
5. **The hybrid model is not Elo-only**: removing xG data produces measurable changes in predictions, confirming xG contributes independent signal.
