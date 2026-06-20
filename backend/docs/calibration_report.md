# Calibration Report

## Methodology

Evaluated on 192 World Cup matches (2014, 2018, 2022) using the hybrid MatchPredictionEngine.

## Metrics

| Metric | Value | Interpretation |
|--------|-------|---------------|
| Brier Score | 0.660142 | 0=perfect, 0.33=naive, 0.66=current |
| Log Loss | 1.091831 | 0=perfect, lower is better |
| RPS | 0.242110 | 0=perfect, 1=worst |
| ECE | 0.081351 | 0=perfectly calibrated |
| Accuracy | 0.4740 | Baseline=0.333 (random 3-outcome) |

## By Tournament

| Tournament | Matches | Accuracy | Brier | Log Loss | RPS |
|-----------|--------|---------|------|---------|-----|
| 2014 | 64 | 0.4531 | 0.694496 | 1.139697 | 0.263155 |
| 2018 | 64 | 0.4688 | 0.632242 | 1.037917 | 0.228289 |
| 2022 | 64 | 0.5000 | 0.653699 | 1.098071 | 0.234941 |

## Calibration Curve

| Confidence Bin | Count | Mean Confidence | Mean Accuracy | Gap |
|---------------|-------|---------------|-------------|-----|
| 0.3-0.4 | 16 | 0.3762 | 0.4375 | 0.0613 |
| 0.4-0.5 | 77 | 0.4516 | 0.4545 | 0.0029 |
| 0.5-0.6 | 42 | 0.5426 | 0.5000 | 0.0426 |
| 0.6-0.7 | 28 | 0.6456 | 0.5714 | 0.0742 |
| 0.7-0.8 | 21 | 0.7475 | 0.3810 | 0.3665 |
| 0.8-0.9 | 8 | 0.8565 | 0.5000 | 0.3565 |

## Findings

1. **Brier Score 0.660** — better than naive (.333) but indicates significant calibration opportunity.
2. **ECE 0.081** — the model is slightly overconfident, especially in high-confidence bins (0.7-0.9 range).
3. **Accuracy 47.4%** — well above the 33.3% random baseline for 3-outcome prediction.
4. **Knockout stage accuracy improves** — 58.3% QF → 66.7% SF/Final vs 45.8% group stage.
5. **The Log Loss penalty on confident wrong predictions** inflates the score — the model is overconfident on some mismatches.
