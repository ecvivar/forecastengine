# Stress Reduction Experiments

| Config | Stress Std | ECE | Brier | Accuracy |
|--------|------------|-----|-------|----------|
| A - Current Production | 0.0576 | 0.0573 | 0.5983 | 0.5312 |
| B - Limit StrengthDiff <= 30% | 0.0598 | 0.0568 | 0.6037 | 0.5208 |
| C - Limit BayesianElo <= 30% | 0.0556 | 0.0816 | 0.5961 | 0.5573 |
| D - Regularized Ensemble | 0.0577 | 0.0579 | 0.6004 | 0.5312 |