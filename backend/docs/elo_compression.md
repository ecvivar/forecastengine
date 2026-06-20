# Elo Compression Experiment

## Results
| Config | Brier | LogLoss | ECE | Accuracy |
|--------|-------|---------|-----|----------|
| Baseline | 0.598 | 1.003 | 0.060 | 0.526 |
| tanh/100 | 0.626 | 1.0397 | 0.0229 | 0.4688 |
| tanh/150 | 0.6197 | 1.0308 | 0.0102 | 0.4844 |
| tanh/200 | 0.6159 | 1.0254 | 0.0199 | 0.4844 |
| tanh/250 | 0.614 | 1.0228 | 0.0234 | 0.4844 |
| tanh/300 | 0.6131 | 1.0216 | 0.0287 | 0.4896 |

## Conclusions
1. Do NOT apply Elo compression -- worsens Brier (best=0.613 vs 0.598)
2. Compression trades accuracy for calibration (false improvement)
3. Reduce elo_weight instead of compressing Elo
