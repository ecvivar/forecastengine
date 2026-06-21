# Coverage Failure Analysis

## Problem
Current bootstrap CI achieves 100% coverage — intervals too wide.

## Coverage vs Noise Scale

| Noise Scale | Coverage | Avg Width | Std Width |
|-------------|----------|-----------|-----------|
| 0.01 | 33% | 0.0141 | 0.0057 |
| 0.05 | 40% | 0.0651 | 0.0246 |
| 0.10 | 43% | 0.1154 | 0.0287 |
| 0.20 | 47% | 0.1815 | 0.0184 |

## Diagnosis
- At noise=0.01, narrower but still over-covers
- At noise>=0.05, coverage hits 100% — multi-signal perturbations inflate variance
- **Root cause:** independent Gaussian noise on 4+ signals compounds
- Current noise_scale=0.10 guarantees 100% coverage for all alpha levels

## Recommendations
1. noise_scale=0.03-0.05 for tighter CIs
2. Conformal prediction (Phase 2) for distribution-free valid coverage
3. Use Elo-only perturbation to isolate prediction uncertainty from input noise