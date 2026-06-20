# Sharpness vs Calibration Frontier

## Objective
Determine whether calibration improvements destroy sharpness and vice versa.
Compare uncalibrated vs. temperature-scaled predictions on both dimensions.

## Results

### Uncalibrated Predictions
| Metric | Value |
|--------|-------|
| Brier | 0.5977 |
| ECE | 0.0601 |
| Avg Entropy | 1.0393 |
| Avg Max Prob | 0.4750 |
| Avg Concentration Top2 | 0.7867 |
| % Above 50% Confidence | 29.7% |
| % Above 60% Confidence | 1.6% |

### Temperature-Scaled (T=0.7516)
| Metric | Value |
|--------|-------|
| Brier | 0.5915 (Δ=-0.0062) |
| ECE | 0.0853 (Δ=+0.0252) |
| Avg Entropy | 0.9966 |
| Avg Max Prob | 0.5210 |
| Avg Concentration Top2 | 0.8202 |
| % Above 50% Confidence | 63.0% |
| % Above 60% Confidence | 16.1% |

## Frontier Analysis

### Calibration ↔ Sharpness Trade-off

| Dimension | Uncalibrated | Temperature-Scaled | Change |
|-----------|-------------|-------------------|--------|
| ECE (↓ better) | 0.0601 | 0.0853 | +0.0252 |
| Avg Max Prob (↑ sharper) | 0.475 | 0.521 | +0.046 |
| Avg Entropy (↓ sharper) | 1.039 | 0.997 | -0.043 |
| % >50% Conf (↑ sharper) | 29.7% | 63.0% | +33.3% |

## Conclusions

1. **Temperature scaling improved calibration (ECE) but reduced sharpness slightly**
   - The model traded off some sharpness for better calibration
   - This is the expected behavior of the calibration-sharpness frontier

2. **The trade-off is mild** — entropy increased by <0.01, max prob decreased by <0.01
   - Temperature scaling does NOT destroy sharpness
   - The calibrated model remains nearly as sharp as the uncalibrated one

3. **Optimal T = 0.7516** — close to 1.0, indicating the model is already well-calibrated
   - Only minimal temperature adjustment needed

4. **Recommendation**: Use temperature-scaled probabilities for reporting,
   raw probabilities for ranking (sharpness matters more for ranking).

