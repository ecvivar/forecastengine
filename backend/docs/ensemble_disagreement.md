# Ensemble Disagreement Metric

## Definition
Ensemble disagreement = std(probabilities) across 4 models.

| Home | Away | Std(HW) | Std(D) | Std(AW) | Entropy | Pairwise KL |
|------|------|---------|--------|---------|---------|-------------|
| H0 | A0 | 0.1296 | 0.0215 | 0.1173 | 1.0385 | -0.031337 |
| H1 | A1 | 0.0595 | 0.0076 | 0.1272 | 1.0618 | -0.070950 |
| H2 | A2 | 0.0808 | 0.0265 | 0.1210 | 1.0634 | -0.045809 |
| H3 | A3 | 0.1219 | 0.0381 | 0.0652 | 1.0270 | -0.029898 |
| H4 | A4 | 0.0660 | 0.0094 | 0.1598 | 1.0094 | -0.035759 |
| H5 | A5 | 0.0546 | 0.0230 | 0.1295 | 1.0371 | -0.072421 |
| H6 | A6 | 0.1410 | 0.0259 | 0.1035 | 1.0430 | -0.012720 |
| H7 | A7 | 0.0782 | 0.0117 | 0.0500 | 1.0634 | -0.099594 |
| H8 | A8 | 0.1641 | 0.0266 | 0.1278 | 1.0440 | -0.005166 |
| H9 | A9 | 0.0562 | 0.0157 | 0.0840 | 1.0784 | -0.100452 |

**Mean Std(HW):** 0.0952
**Mean Pairwise KL:** -0.050411

## Integration
Ensemble disagreement should be the primary uncertainty proxy:
- High disagreement = high uncertainty
- Low disagreement = high confidence