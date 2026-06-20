# FIFA Signal Audit

## Results
| Metric | WITH FIFA | WITHOUT FIFA | Delta | Winner |
|--------|-----------|-------------|-------|--------|
| brier | 0.5977 | 0.6209 | -0.0232 | WITH FIFA |
| logloss | 1.0026 | 1.0329 | -0.0303 | WITH FIFA |
| ece | 0.0601 | 0.057 | +0.0031 | WITHOUT |
| accuracy | 0.526 | 0.4948 | +0.0312 | WITH FIFA |

## Verdict
1. FIFA IS useful -- removing it worsens Brier by 0.023
2. FIFA is NOT redundant with Elo
3. Keep FIFA weight at 0.10
