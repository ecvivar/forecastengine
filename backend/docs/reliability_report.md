# Reliability Report

## Objective
Evaluate calibration quality by grouping predictions into 10 bins (0-10%, 10-20%, ..., 90-100%)
and measuring predicted vs. observed frequency per bin.

## Results

### Overall Metrics
| Metric | Value |
|--------|-------|
| ECE (overall) | 0.0509 |
| MCE (overall) | 0.2106 |
| Target ECE | ≤ 0.05 |
| Passes | False |
| Number of Bins | 10 |

### Home Win
ECE: 0.0774, MCE: 0.2106

| Bin | Count | Predicted Freq | Observed Freq | Error | Abs Error |
|-----|-------|---------------|--------------|-------|-----------|
| 0-10% | 0 | 0.0500 | 0.0000 | +0.0000 | 0.0000 |
| 10-20% | 0 | 0.1500 | 0.0000 | +0.0000 | 0.0000 |
| 20-30% | 14 | 0.2820 | 0.0714 | -0.2106 | 0.2106 |
| 30-40% | 55 | 0.3538 | 0.3091 | -0.0447 | 0.0447 |
| 40-50% | 72 | 0.4550 | 0.5000 | +0.0450 | 0.0450 |
| 50-60% | 48 | 0.5402 | 0.6667 | +0.1265 | 0.1265 |
| 60-70% | 3 | 0.6221 | 0.6667 | +0.0446 | 0.0446 |
| 70-80% | 0 | 0.7500 | 0.0000 | +0.0000 | 0.0000 |
| 80-90% | 0 | 0.8500 | 0.0000 | +0.0000 | 0.0000 |
| 90-100% | 0 | 0.9500 | 0.0000 | +0.0000 | 0.0000 |

### Draw
ECE: 0.0193, MCE: 0.0506

| Bin | Count | Predicted Freq | Observed Freq | Error | Abs Error |
|-----|-------|---------------|--------------|-------|-----------|
| 0-10% | 0 | 0.0500 | 0.0000 | +0.0000 | 0.0000 |
| 10-20% | 37 | 0.1926 | 0.2432 | +0.0506 | 0.0506 |
| 20-30% | 155 | 0.2183 | 0.2065 | -0.0118 | 0.0118 |
| 30-40% | 0 | 0.3500 | 0.0000 | +0.0000 | 0.0000 |
| 40-50% | 0 | 0.4500 | 0.0000 | +0.0000 | 0.0000 |
| 50-60% | 0 | 0.5500 | 0.0000 | +0.0000 | 0.0000 |
| 60-70% | 0 | 0.6500 | 0.0000 | +0.0000 | 0.0000 |
| 70-80% | 0 | 0.7500 | 0.0000 | +0.0000 | 0.0000 |
| 80-90% | 0 | 0.8500 | 0.0000 | +0.0000 | 0.0000 |
| 90-100% | 0 | 0.9500 | 0.0000 | +0.0000 | 0.0000 |

### Away Win
ECE: 0.0561, MCE: 0.1967

| Bin | Count | Predicted Freq | Observed Freq | Error | Abs Error |
|-----|-------|---------------|--------------|-------|-----------|
| 0-10% | 0 | 0.0500 | 0.0000 | +0.0000 | 0.0000 |
| 10-20% | 2 | 0.1967 | 0.0000 | -0.1967 | 0.1967 |
| 20-30% | 57 | 0.2606 | 0.1579 | -0.1027 | 0.1027 |
| 30-40% | 79 | 0.3425 | 0.3544 | +0.0119 | 0.0119 |
| 40-50% | 48 | 0.4498 | 0.5000 | +0.0502 | 0.0502 |
| 50-60% | 6 | 0.5298 | 0.3333 | -0.1965 | 0.1965 |
| 60-70% | 0 | 0.6500 | 0.0000 | +0.0000 | 0.0000 |
| 70-80% | 0 | 0.7500 | 0.0000 | +0.0000 | 0.0000 |
| 80-90% | 0 | 0.8500 | 0.0000 | +0.0000 | 0.0000 |
| 90-100% | 0 | 0.9500 | 0.0000 | +0.0000 | 0.0000 |

## Analysis

### Overall ECE = 0.0509
The model is **ABOVE** (fails) the 0.05 target threshold.

### Per-Bin Calibration
- **Extreme bins (0-10%, 90-100%)**: Typically show the largest calibration errors
  because few predictions fall in these ranges
- **Mid-range bins (30-70%)**: Better calibrated due to more samples
- **Draw predictions**: Usually hardest to calibrate due to lower frequency

### MCE (Maximum Calibration Error) = 0.2106
MCE identifies the worst-calibrated bin. The bin with highest absolute error
should be investigated for systematic bias.

## Conclusions
1. Overall calibration error (ECE = 0.0509) barely misses the ECE ≤ 0.05 criterion (target: 0.050).
2. Maximum bin error (MCE = 0.2106) may indicate systematic bias in extreme predictions
3. Temperature scaling (T=0.7516) improved calibration for mid-range bins but
   potentially degraded extreme bins (see Sharpness vs Calibration report)
4. Reliability can be improved by:
   - Histogram binning / Platt scaling on a held-out set
   - Isotonic regression for non-parametric calibration
   - Temperature scaling with optimized T per competition

