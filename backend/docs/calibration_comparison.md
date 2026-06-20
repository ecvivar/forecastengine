# Probabilistic Calibration Comparison

## Methods

Three calibration techniques were applied to the Sprint 4A model's 192 match predictions:

- **Platt Scaling**: Logistic regression on logits (optimizes a, b parameters)
- **Isotonic Regression**: Pool Adjacent Violators (PAVA) with 20 bins
- **Temperature Scaling**: Single T parameter scaling logits

## Results

| Metric | Before | Platt | Isotonic | Temperature |
|--------|--------|-------|----------|-------------|
| brier | 0.610862 | 0.610862 | 0.610862 | 0.610802 |
| log_loss | 1.018512 | 1.018505 | 1.018505 | 1.018427 |
| rps | 0.220329 | 0.220329 | 0.220329 | 0.220291 |
| ece | 0.061117 | 0.061119 | 0.061119 | 0.051567 |

## Analysis

1. **Temperature Scaling (T=1.03) is the most effective** — improves ECE from 0.061 to 0.052
2. **Platt Scaling has minimal effect** (a≈1.32, b≈-0.11) — the model logits are already well-scaled
3. **Isotonic Regression** performs similarly to Platt (limited benefit)
4. **The model is already reasonably calibrated** — Bayesian prior serves as a natural regularization
5. **T≈1.03 confirms** that the model is only slightly overconfident (needs T>1 to spread probabilities)
6. **Recommendation**: Apply Temperature Scaling with T=1.03 in production for optimal calibration