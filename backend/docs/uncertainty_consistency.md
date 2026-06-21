# Uncertainty Consistency Audit

**Sample Size:** 20 matches

- **Mean Uncertainty:** 0.8259 (std=0.0733)
- **Mean CI Width:** 0.1074 (std=0.0120)
- **Mean Entropy:** 1.0394

## Correlations
- **Spearman(Uncertainty, CI Width):** 0.1143
- **Spearman(Entropy, CI Width):** 0.0947
- **Spearman(Uncertainty, Entropy):** 0.8466

**Target:** Correlation > 0.70 -> **FAIL**
**Interpretation:** Weak - uncertainty and CI width are poorly aligned.