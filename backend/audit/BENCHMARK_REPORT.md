# Benchmark Report: Model Comparison

**Date:** 2026-06-09
**Dataset:** 192 historical World Cup matches (2014: 64, 2018: 64, 2022: 64)
**Compare:** 3 prediction model variants

---

## Overall Results

| Model | Brier ↓ | Log Loss ↓ | Accuracy ↑ | ECE ↓ | AUC-ROC ↑ |
|-------|---------|------------|------------|-------|-----------|
| Pure Poisson | **0.9407** | **1.5862** | **18.23%** | **38.59%** | **0.352** |
| Poisson + Dixon-Coles | **0.5510** | **0.9427** | **57.29%** | **9.83%** | **0.698** |
| Full Model (DC + Bayes) | 0.5567 | 0.9655 | 56.25% | **5.47%** | 0.698 |

**Ranking by Brier Score:** Dixon-Coles > Full Model >> Pure Poisson
**Improvement vs Poisson:** DC: -41.4%, Full: -40.8%

---

## Per-Tournament Breakdown

### 2014 World Cup (Brazil)

| Model | Brier | Accuracy |
|-------|-------|----------|
| Poisson | 0.9463 | 15.62% |
| Dixon-Coles | **0.5166** | **60.94%** |
| Full | 0.5224 | 59.38% |

### 2018 World Cup (Russia)

| Model | Brier | Accuracy |
|-------|-------|----------|
| Poisson | 0.9545 | 21.88% |
| Dixon-Coles | **0.5593** | **56.25%** |
| Full | 0.5550 | **59.38%** |

### 2022 World Cup (Qatar)

| Model | Brier | Accuracy |
|-------|-------|----------|
| Poisson | 0.9215 | 17.19% |
| Dixon-Coles | **0.5772** | **54.69%** |
| Full | 0.5929 | 50.00% |

---

## Per-Stage Breakdown

| Stage | Poisson Brier | DC Brier | Full Brier | Best |
|-------|--------------|----------|------------|------|
| Group | 0.9270 | 0.5591 | 0.5852 | DC |
| Round of 16 | 1.0874 | **0.4649** | 0.4112 | Full |
| Quarter-final | 0.9024 | **0.6617** | 0.5949 | Full |
| Semi-final | 0.8770 | **0.4894** | 0.4469 | Full |
| Final | 0.9234 | **0.5186** | 0.4267 | Full |
| Third place | 0.7233 | **0.5645** | 0.5536 | Full |

---

## Analysis

### Why Pure Poisson Fails (Brier 0.94)

Pure Poisson without the Dixon-Coles low-score correction:
1. **Overestimates 0-0 draws**: P(0-0) = exp(-λh) × exp(-λa) which is ~10-15% for typical λ values
2. **Underestimates 1-0/0-1 wins**: The correction term `(1+ρ)` for these scores is absent
3. **Poor discrimination**: The modal predicted outcome is often a draw (especially for balanced matches), inflating the Brier score when matches produce a winner
4. **Accuracy collapses to 18%** (worse than guessing 33% randomly)

### Why Dixon-Coles Wins on Brier

The DC correction (τ=0.1):
- Reduces 0-0 probability by factor `(1-τ) = 0.9`
- Increases 1-0 and 0-1 probabilities by factor `(1+τ) = 1.1`
- This small adjustment dramatically improves the marginal probability distribution
- Result: Brier drops from 0.94 to 0.55 (-41.4%)

### Why Full Model Wins on Calibration

The Bayesian update (Elo prior + DC likelihood):
- Smooths extreme predictions toward the Elo-based prior
- This reduces the 70-80% overconfidence (from DC alone) to more reasonable levels
- ECE improves from 9.83% (DC) to 5.47% (Full) — a 44% improvement
- But Brier slightly increases (0.551 → 0.557) because the prior adds bias for extreme matches

---

## Recommendations

1. **Use the Full Model for production.** While DC has marginally better Brier (0.551 vs 0.557), the Full Model's superior calibration (ECE 5.47% vs 9.83%) means its probability estimates are more trustworthy for decision-making.

2. **Never use pure Poisson alone.** The DC correction is a mandatory requirement for football prediction.

3. **Consider calibration adjustments.** The small home bias (+3.89%) and draw bias (+2.44%) can be corrected with `home_advantage_adjustment: -0.019` and `draw_adjustment: -0.012`.

4. **Confederation-specific monitoring.** Monitor AFC and CAF predictions separately as they show larger biases.
