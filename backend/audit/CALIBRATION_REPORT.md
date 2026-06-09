# Calibration Report

**Date:** 2026-06-09
**Dataset:** 192 historical World Cup matches (2014, 2018, 2022)
**Engine:** `CalibrationEngine` with `MatchPredictionEngine` (Full Model)

---

## 1. Global Metrics (Full Model)

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Brier Score** | 0.5567 | Lower is better (0=perfect, 0.667=random, 2=worst) |
| **Log Loss** | 0.9655 | Lower is better (0=perfect, unbounded above) |
| **Accuracy** | 56.25% | Correct outcome class prediction rate |
| **ECE** | 5.47% | Expected Calibration Error (lower is better) |
| **AUC-ROC** | 0.698 | 0.5=random, 1.0=perfect (moderately discriminative) |

### Per Tournament

| Tournament | Matches | Brier | Accuracy | ECE | AUC-ROC |
|------------|---------|-------|----------|-----|---------|
| 2014 | 64 | 0.5224 | 59.38% | 11.41% | 0.716 |
| 2018 | 64 | 0.5550 | 59.38% | 11.12% | 0.657 |
| 2022 | 64 | 0.5929 | 50.00% | 11.34% | 0.708 |

### Per Stage

| Stage | Matches | Brier | Accuracy |
|-------|---------|-------|----------|
| Group | 144 | 0.5852 | 53.47% |
| Round of 16 | 24 | 0.4112 | 70.83% |
| Quarter-final | 12 | 0.5949 | 50.00% |
| Semi-final | 6 | 0.4469 | 66.67% |
| Final | 3 | 0.4267 | 66.67% |
| Third place | 3 | 0.5536 | 66.67% |

---

## 2. 3-Model Benchmark

| Model | Brier | Log Loss | Accuracy | ECE | AUC-ROC | Improvement |
|-------|-------|----------|----------|-----|---------|-------------|
| **Pure Poisson** | 0.9407 | 1.5862 | 18.23% | 38.59% | 0.352 | baseline |
| **Dixon-Coles** | **0.5510** | **0.9427** | **57.29%** | 9.83% | **0.698** | **+41.4%** |
| **Full Model** | 0.5567 | 0.9655 | 56.25% | **5.47%** | **0.698** | +40.8% |

**Best model by Brier Score:** Dixon-Coles
**Best calibrated (ECE):** Full Model

### Key Findings
- Pure Poisson without Dixon-Coles correction is **worse than random** (Brier 0.94 vs random 0.667). The low-score correction is essential for football prediction.
- Dixon-Coles improves Brier by **41.4%** over pure Poisson.
- The Full Model (DC + Bayesian update) has **better calibration (ECE 5.47%)** than DC alone (9.83%), meaning its probability estimates are more reliable.
- The Bayesian prior slightly smooths extreme predictions, reducing Brier by 0.0057 but improving ECE by 4.36 percentage points.

---

## 3. Bias Analysis

### Home Team Bias
| Metric | Value |
|--------|-------|
| Predicted home win rate | 49.72% |
| Actual home win rate | 45.83% |
| **Bias** | **+3.89%** (overpredicts) |

The model systematically overpredicts the first-listed team's win probability. This is expected since "home" team in World Cup data is determined by fixture listing, not actual home advantage. The Elo rating difference and Bayesian prior both favor the higher-rated team, which tends to be listed first.

### Draw Bias
| Metric | Value |
|--------|-------|
| Predicted draw rate | 23.79% |
| Actual draw rate | 21.35% |
| **Bias** | **+2.44%** (overpredicts) |

The model slightly overpredicts draws. This is common in Poisson-based models where the diagonal of the scoring matrix accumulates probability mass.

### Favorite Over-/Under-confidence

| Probability Bracket | Count | Avg Predicted | Actual Win Rate | Gap |
|---------------------|-------|---------------|-----------------|-----|
| 0.0 - 0.4 | 15 | 0.388 | 0.333 | +0.055 (over) |
| 0.4 - 0.5 | 34 | 0.452 | 0.324 | +0.128 (over) |
| 0.5 - 0.6 | 45 | 0.554 | 0.533 | +0.020 (over) |
| 0.6 - 0.7 | 43 | 0.668 | 0.674 | -0.007 (under) |
| 0.7 - 0.8 | 46 | 0.749 | 0.674 | +0.075 (over) |
| 0.8 - 0.9 | 9 | 0.811 | 0.889 | -0.078 (under) |

**Pattern:** The model is overconfident in the 40-50% and 70-80% ranges, but underconfident in the 80-90% range.

### Confederation Bias

| Confederation | Matches | Brier | Accuracy | Home Win Pred | Home Win Actual | Fav Pred | Fav Acc | Draw Pred | Draw Actual |
|--------------|---------|-------|----------|---------------|-----------------|----------|---------|-----------|-------------|
| AFC | 49 | 0.5773 | 53.06% | 0.361 | 0.296 | 0.616 | 0.531 | 0.263 | 0.245 |
| CAF | 52 | 0.5698 | 55.77% | 0.315 | 0.231 | 0.575 | 0.558 | 0.256 | 0.192 |
| CONCACAF | 39 | 0.5631 | 56.41% | 0.346 | 0.385 | 0.620 | 0.564 | 0.230 | 0.179 |
| CONMEBOL | 66 | 0.5448 | 59.09% | 0.604 | 0.591 | 0.622 | 0.591 | 0.218 | 0.212 |
| UEFA | 146 | 0.5566 | 55.48% | 0.552 | 0.507 | 0.611 | 0.555 | 0.242 | 0.219 |

**Notes:**
- CONMEBOL (South America) shows the highest accuracy (59.09%) and best Brier (0.5448)
- AFC (Asia) teams are most overpredicted as home winners (+6.5% bias)
- CAF (Africa) teams show the largest draw overprediction (+6.4% bias)
- UEFA (Europe) has the most matches (146) and near-average metrics

### Confidence- Stratified Accuracy

| Confidence Level | Accuracy |
|------------------|----------|
| High (CI > 65) | 100.00% |
| Low (CI < 35) | 52.98% |
| Favorite (>0.5 prob) | 64.34% |
| Underdog (<0.5 prob) | 32.65% |

---

## 4. Calibration Curve

| Bin | Count | Mean Predicted | Mean Actual | Gap |
|-----|-------|----------------|-------------|-----|
| 0.30 - 0.40 | 15 | 0.388 | 0.333 | +0.055 |
| 0.40 - 0.50 | 34 | 0.452 | 0.324 | +0.128 |
| 0.50 - 0.60 | 45 | 0.554 | 0.533 | +0.020 |
| 0.60 - 0.70 | 43 | 0.668 | 0.674 | -0.007 |
| 0.70 - 0.80 | 46 | 0.749 | 0.674 | +0.075 |
| 0.80 - 0.90 | 9 | 0.811 | 0.889 | -0.078 |

The model is reasonably well-calibrated in the 50-70% confidence range (within 2 percentage points). Overconfidence is visible in the 40-50% and 70-80% ranges.

---

## 5. Suggested Adjustments

| Adjustment | Value | Rationale |
|------------|-------|-----------|
| `home_advantage_adjustment` | -0.0194 | Reduce home win predictions by ~2% to correct home bias |
| `draw_adjustment` | -0.0122 | Reduce draw predictions by ~1.2% to correct draw overprediction |

---

## 6. Conclusions

1. **Model is historically calibrated.** Brier Score of 0.5567 (vs 0.667 random) and Accuracy of 56.25% demonstrate meaningful predictive power across 192 matches and 3 World Cups.

2. **Dixon-Coles is essential.** The +41.4% improvement over pure Poisson confirms that the low-score correction is mandatory for football prediction.

3. **Calibration is reasonable.** ECE of 5.47% means the model's confidence estimates are within ~5% of actual outcomes on average.

4. **Small biases exist.** Home win overprediction (+3.89%) and draw overprediction (+2.44%) are systematic but small. Suggested adjustments are conservative (-1.9% and -1.2% respectively).

5. **Confederation differences.** The model performs best for CONMEBOL teams (59.1% accuracy) and worst for AFC teams (53.1%), likely due to Elo rating accuracy differences across confederations.

6. **Knockout stages are more predictable.** Round of 16 has the highest accuracy (70.83%), while group stage (53.47%) and quarter-finals (50.0%) are harder to predict due to more balanced matchups.
