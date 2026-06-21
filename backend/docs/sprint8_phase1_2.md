# Phase 1-2: Weight Optimization & EliteScore

## Weight Sweep Results

| elo_weight | Accuracy | Brier | LogLoss | ECE | Stress_Std | PartialEliteScore |
|------------|----------|-------|---------|-----|------------|-------------------|
| 0.40 | 0.4844 | 0.6109 | 1.0185 | 0.0611 | 0.0985 | 0.4547 |
| 0.38 | 0.4948 | 0.6123 | 1.0205 | 0.0341 | 0.0930 | 0.5314 |
| 0.36 | 0.4948 | 0.6139 | 1.0225 | 0.0309 | 0.0907 | 0.5325 |

**Best elo_weight:** 0.36

**Full EliteScore (with tournament):** 0.5336