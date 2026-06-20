# Sprint 6 — Robustness, Reliability & Probabilistic Validation

## Final Report

Generated: June 2026

---

## Executive Summary

Sprint 6 focused on converting the predictive engine from "functionally correct" to
**"robust, reliable, and statistically validated"**. We conducted 10 phases covering
sensitivity decomposition, root cause analysis, uncertainty propagation, CI coverage,
reliability diagrams, k-fold backtesting, weight stability, sharpness vs. calibration,
tournament robustness, and production readiness.

### Key Results

| Criterion | Target | Actual | Status |
|-----------|--------|--------|--------|
| Stress Std | < 0.050 | **0.092** | ❌ |
| CI Coverage (synthetic) | 85-95% | **100%** | ⚠️ Over-covered |
| ECE | ≤ 0.05 | **0.051** | ⚠️ Borderline |
| K-Fold Brier Std | < 0.02 | **0.029** | ⚠️ Moderate |
| Tournament 10k sufficient | Yes | **Yes** | ✅ |
| Drivers Sum 100% | Yes | **Yes** | ✅ |
| Production Readiness | ≥ 60/100 | **58.8/100** | ⚠️ Near threshold |

---

## Phase Results

### FASE 1 — Sensitivity Decomposition
- **Elo Elasticity**: 3.19% probability change per 1% Elo change
- **xG For Elasticity**: 1.12%, **xG Against**: 1.08%
- **FIFA Rank**: 0.0% — saturated by normalization clamp
- **Home Advantage**: 0.62% — stable, low variance
- **[Full Report](sensitivity_decomposition.md)**

### FASE 2 — Stress Root Cause
- **Primary cause**: Elo (39% of explained variance)
- **Secondary**: xG For (19%), xG Against (8%)
- **Negligible**: FIFA Rank (0%), Home Advantage (9%)
- **Root cause**: Elo's high weight (0.40) amplifies noise
- **[Full Report](stress_root_cause.md)**

### FASE 3 — Uncertainty Propagation
- Brier before: 0.598 → after: 0.595 (no degradation)
- LogLoss before: 1.003 → after: 0.999 (slight improvement)
- ECE before: 0.060 → after: 0.069 (slight increase)
- **Finding**: Sampling team strength ~N(mean, RD) does not meaningfully affect
  predictive metrics. The existing rating_deviation values (default 35) are too
  small to create meaningful perturbations.

### FASE 4 — CI Coverage
- Synthetic coverage: 100% (over-covered — CIs wider than needed)
- Empirical coverage: 100% (point estimate always within CI)
- Avg CI width: 0.083 (synthetic), 0.045 (empirical)
- **Finding**: Bootstrap CIs are conservative. Binary outcome coverage is not
  a meaningful metric for probability prediction.
- **[Full Report](coverage_validation.md)**

### FASE 5 — Reliability Diagrams
- **Overall ECE**: 0.051 (barely above 0.050 target)
- **Overall MCE**: 0.211 (worst bin shows significant error)
- **Bin analysis**: Extreme bins (0-10%, 90-100%) show largest errors
- **[Full Report](reliability_report.md)**

### FASE 6 — K-Fold Backtesting
- Mean val Brier: 0.597, Std: 0.029
- Mean val LogLoss: 0.997, Std: 0.035
- **K=5 stable performance**, no severe overfitting
- **[Full Report](kfold_validation.md)**

### FASE 7 — Weight Stability
- **Most critical weight**: Elo (±10% → significant Brier change)
- **Most robust**: xG Defense (small weight buffers impact)
- **Finding**: Current weights are near-optimal at 0.40/0.30/0.10/0.20
- **[Full Report](weight_stability.md)**

### FASE 8 — Sharpness vs. Calibration
- Temperature scaling (T=0.75) improved calibration slightly
- Sharpness impact: minimal (entropy +0.001, max prob -0.002)
- **Finding**: No significant trade-off — both can coexist
- **[Full Report](calibration_sharpness.md)**

### FASE 9 — Tournament Robustness
- **10,000 simulations**: CI width = ±0.5% for 12% probability
- **Convergence**: Follows √(n) per CLT
- **Verdict**: 10k is sufficient for production
- **[Full Report](tournament_robustness.md)**

### FASE 10 — Production Readiness
| Category | Score |
|----------|-------|
| Predictive Quality | 67.7/100 |
| Calibration | 59.9/100 |
| Reliability | 66.1/100 |
| Robustness | 38.5/100 |
| Explainability | 92.0/100 |
| Uncertainty Quantification | 50.0/100 |
| Operational Stability | 85.0/100 |
| **Overall** | **58.8/100** |
- **[Full Report](production_readiness.md)**

---

## Success Criteria Validation

| Criterion | Target | Result | Verdict |
|-----------|--------|--------|---------|
| Stress Std | < 0.050 | 0.092 | ❌ **Miss** |
| CI Coverage | 85-95% | 100% | ⚠️ **Over-covered** |
| ECE | ≤ 0.05 | 0.051 | ⚠️ **Borderline miss** |
| K-Fold Stability | Low std | 0.029 | ⚠️ **Moderate** |
| Tournament 10k valid | Yes | Yes | ✅ **Pass** |
| Explainability sum 100% | Yes | Yes | ✅ **Pass** |

**Overall Sprint 6 Verdict**: ⚠️ PARTIALLY SUCCESSFUL
- 2/6 criteria pass
- 3/6 are borderline or over-covered
- 1/6 (stress std) clearly misses

---

## Quantitative Answers

### 1. How calibrated are the probabilities?
**ECE = 0.051** — borderline. The model is well-calibrated for mid-range
probabilities (30-70%) but shows errors in extreme bins (0-10%, 90-100%).
Temperature scaling (T=0.75) provides marginal improvement.

### 2. How robust are predictions to perturbations?
**Stress std = 0.092** — exceeds target of 0.050. The primary cause is Elo's
high sensitivity (elasticity 3.19). Perturbing Elo by ±15% changes home win
probability by ~3.6 percentage points.

### 3. Which variables generate the most sensitivity?
**Elo dominates** (mean sensitivity 3.19), followed by **xG For** (1.12) and
**xG Against** (1.08). **FIFA Rank shows zero sensitivity** due to normalization
clamping — this is a data quality issue, not a robustness one.

### 4. How reliable are the confidence intervals?
**Conservative (100% coverage)**. Bootstrap CIs are wider than necessary for
90% nominal coverage. Avg width = 0.04-0.08 (reasonable). The intervals are
valid but slightly over-conservative.

### 5. Is the system ready for production?
**Near production (58.8/100)**. The system is strong in explainability (92/100)
and operational stability (85/100). The main gaps are:
- **Robustness** (38.5/100) — stress std must be reduced
- **Uncertainty Quantification** (50/100) — CI width calibration
- **Calibration** (59.9/100) — borderline ECE

### 6. What statistical limitations remain?
1. **Bootstrap CI over-coverage** — needs noise calibration
2. **FIFA rank saturation** — normalization limits signal
3. **Extreme bin calibration error** — contributes to MCE=0.211
4. **Historical xG estimation** — pre-2026 xG = avg goals, a coarse proxy
5. **Small historical dataset** — limits k-fold depth and statistical power

### 7. What improvements would yield the highest ROI?
1. **Reduce Elo weight (0.30)** — lowers stress std from 0.092 toward 0.050
2. **Add Elo smoothing/decay** — prevents large Elo swings
3. **Calibrate bootstrap noise** — hit 90% CI coverage exactly
4. **Extreme bin calibration** — Platt scaling or iso regression
5. **Unbound FIFA normalization** — restore FIFA rank as a signal

---

## Files Modified/Created

### New Files
- `app/validation/sensitivity_decomposition.py` — Sensitivity analysis
- `app/validation/coverage_validation.py` — CI coverage validator
- `app/validation/reliability.py` — Reliability diagrams
- `scripts/sprint6_validation.py` — Master validation runner
- `scripts/sprint6_reports.py` — Report generation
- `docs/sprint6_data.json` — Validation data
- `docs/sensitivity_decomposition.md`
- `docs/stress_root_cause.md`
- `docs/coverage_validation.md`
- `docs/reliability_report.md`
- `docs/kfold_validation.md`
- `docs/weight_stability.md`
- `docs/calibration_sharpness.md`
- `docs/tournament_robustness.md`
- `docs/production_readiness.md`

### Modified Files
- `app/engine/meta_ensemble.py` — Improved `bootstrap_ci` with signal perturbation
- `app/validation/__init__.py` — Added new exports

---

*Sprint 6 completed. Transitioning to Sprint 7: Direct Calibration & Real-Time Data.*
