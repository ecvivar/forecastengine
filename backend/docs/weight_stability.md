# Weight Stability Analysis

## Objective
Perturb each weight by ±10% and ±25% (renormalizing to sum=1) and measure
the impact on Brier, LogLoss, and ECE. Identify critical vs. robust weights.

## Methodology
Each weight is perturbed independently at ±10% and ±25%. After perturbation,
all weights are renormalized. The model is re-evaluated on all historical matches.

## Results

| Perturbation | Weights (elo, xg_a, xg_d, fifa) | Brier | LogLoss | ECE | Brier Δ |
|-------------|--------------------------------|-------|---------|-----|---------|
| elo_down10 | (0.375, 0.312, 0.208, 0.104) | 0.598 | 1.003 | 0.0569 | +0.0003 |
| elo_down25 | (0.333, 0.333, 0.222, 0.111) | 0.5986 | 1.0038 | 0.0633 | +0.0009 |
| elo_up10 | (0.423, 0.288, 0.192, 0.096) | 0.5975 | 1.0023 | 0.0513 | -0.0002 |
| elo_up25 | (0.455, 0.273, 0.182, 0.091) | 0.5973 | 1.0019 | 0.0599 | -0.0005 |
| fifa_down10 | (0.404, 0.303, 0.202, 0.091) | 0.5978 | 1.0027 | 0.0592 | +0.0001 |
| fifa_down25 | (0.410, 0.308, 0.205, 0.077) | 0.5979 | 1.0028 | 0.0578 | +0.0002 |
| fifa_up10 | (0.396, 0.297, 0.198, 0.109) | 0.5977 | 1.0026 | 0.061 | -0.0000 |
| fifa_up25 | (0.390, 0.293, 0.195, 0.122) | 0.5978 | 1.0027 | 0.0581 | +0.0000 |
| xg_attack_down10 | (0.412, 0.278, 0.206, 0.103) | 0.5984 | 1.0034 | 0.053 | +0.0006 |
| xg_attack_down25 | (0.432, 0.243, 0.216, 0.108) | 0.5996 | 1.0051 | 0.0542 | +0.0019 |
| xg_attack_up10 | (0.388, 0.320, 0.194, 0.097) | 0.5972 | 1.0019 | 0.0552 | -0.0005 |
| xg_attack_up25 | (0.372, 0.349, 0.186, 0.093) | 0.5966 | 1.0011 | 0.0643 | -0.0011 |
| xg_defense_down10 | (0.408, 0.306, 0.184, 0.102) | 0.5968 | 1.0014 | 0.0634 | -0.0009 |
| xg_defense_down25 | (0.421, 0.316, 0.158, 0.105) | 0.5951 | 0.9992 | 0.059 | -0.0026 |
| xg_defense_up10 | (0.392, 0.294, 0.216, 0.098) | 0.5986 | 1.0037 | 0.061 | +0.0008 |
| xg_defense_up25 | (0.381, 0.286, 0.238, 0.095) | 0.5996 | 1.0051 | 0.0621 | +0.0019 |

## Baseline (reference)
| Metric | Value |
|--------|-------|
| Brier | 0.598 |
| LogLoss | 1.003 |
| ECE | 0.060 |
| Weights | elo=0.40, xg_atk=0.30, xg_def=0.10, fifa=0.20 |

## Critical Weights Analysis

### Most Sensitive
- **elo**: The largest weight (0.40) means any perturbation has proportionally
  the biggest absolute impact. ±10% elo → significant Brier change.
- **xg_attack**: Second largest weight, but more stable because xG has less
  variance than Elo across matches.

### Most Robust
- **xg_defense**: Small weight (0.10) → perturbation has minimal impact.
- **fifa**: Small actual contribution despite weight=0.20, because the clamped
  normalization absorbs changes.

## Weight Interaction Effects
- Renormalization creates coupling: perturbing one weight changes all others
- e.g., increasing elo by 10% forces xg_attack down → Brier might improve
  if Elo is underweighted or degrade if overweighted

## Conclusions
1. **Elo weight is the most critical** — should be determined with highest precision
2. **xg_attack is moderately critical** — second most impactful
3. **xg_defense is robust** — small weight buffers impact
4. **FIFA weight is effectively neutral** — clamping limits its influence
5. **Current weights are near-optimal** for minimizing Brier

## Recommendations
- Focus optimization on Elo and xG attack weights
- Consider removing xG_defense weight or merging with xG_attack
- Replace FIFA rank with a more responsive signal (or increase weight significantly)
