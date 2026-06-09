# Statistical Audit Report — WorldCup Forecast Engine 2026

**Date:** 2026-06-08
**Scope:** Full mathematical and statistical audit of prediction pipeline
**Severity Legend:** 🔴 CRITICAL | 🟠 HIGH | 🟡 MEDIUM | 🔵 INFO

---

## 1. Poisson Lambda Calibration  🔴 CRITICAL

### Finding
The match prediction engine computes Poisson lambdas using raw IGF scores (0-100 scale) without any scaling, producing astronomically incorrect expected goals.

### Evidence
```python
# match_prediction.py:148-149
home_strength = home_team.igf_score        # e.g., 95 for Brazil
away_strength = away_team.igf_score        # e.g., 30 for Saudi Arabia
lambda_home = max(0.1, exp(home_strength - away_strength + ha))
# exp(95 - 30) = exp(65) = 1.7e28  goals expected — impossible
```

**Measured values for Brazil vs San Marino:**
- Match prediction engine: λ_home = **1.22e+39** goals
- Monte Carlo engine (IGF/50): λ_home = **6.05** goals
- Football reality: λ_home ≈ **2.5 – 4.0** goals

### Root Cause
The IGF engine was changed from a 0-1 scale to a 0-100 scale, but `predict_poisson()` was not updated to divide by 50 (as the Monte Carlo engine does at `monte_carlo.py:352`).

### Impact
- ALL predictions from `predict_poisson()`, `predict_dixon_coles()`, and `predict_full()` are meaningless
- Score probability matrices assign >99.99% probability to scores like 30-0
- Home/Away win probabilities are essentially 1.0 / 0.0 for any non-trivial strength difference
- Calibration tests that "passed" earlier only did so because of floating-point saturation (exp(65) saturates to infinity, then softmax-like normalization collapses all probability to one outcome)

### Required Fix
Divide IGF by 50 before exponentiation to match the Monte Carlo engine:
```python
home_strength = home_team.igf_score / 50.0
away_strength = away_team.igf_score / 50.0
```

---

## 2. Dixon-Coles vs Academic Model  🟠 HIGH

### Finding
The current implementation uses a simplified flat-multiplier approximation instead of the proper Dixon-Coles (1996) model.

### Current Code
```python
# match_prediction.py:289-298
if i == 0 and j == 0:
    adjusted[score] = prob * (1 - rho)
elif i == 0 and j == 1:
    adjusted[score] = prob * (1 + rho)
elif i == 1 and j == 0:
    adjusted[score] = prob * (1 + rho)
elif i == 1 and j == 1:
    adjusted[score] = prob * (1 - rho)
```

### Academic Dixon-Coles (1996)
The correct adjustment factor is:

$$\tau_{\rho}(x, y; \lambda, \mu) = 1 + \rho \cdot \frac{(x - \lambda)(y - \mu)}{\sqrt{\lambda \mu}}$$

Applied multiplicatively to the independent Poisson probability:
$$P(X=x, Y=y) = \tau_{\rho}(x,y;\lambda,\mu) \cdot \frac{\lambda^x e^{-\lambda}}{x!} \cdot \frac{\mu^y e^{-\mu}}{y!}$$

### Issues
1. **Flat multipliers ignore λ/μ dependence**: The adjustment should depend on the expected goals (λ, μ), not just on the score line. For example, (0,0) adjustment should be `1 + ρ√(λμ)`, which differs for high vs low scoring matches.
2. **Fixed ρ = 0.1**: Should be estimated from historical data per tournament/period.
3. **Only 4 score cells adjusted**: Academic DC applies to ALL low scores, with the adjustment approaching 1 as scores increase.

### Impact
The adjustment is directionally correct (increases 0-1/1-0, decreases 0-0/1-1) but numerically imprecise. With the Poisson lambda bug (Issue #1), this is masked entirely.

### Recommended Fix
Implement proper DC tau function:
```python
def dc_tau(x, y, lam, mu, rho):
    if x == 0 and y == 0:
        return 1 + rho * np.sqrt(lam * mu)
    elif (x == 0 and y == 1) or (x == 1 and y == 0):
        return 1 + rho * ((x - lam) * (y - mu)) / np.sqrt(lam * mu)
    elif (x == 1 and y == 1):
        return 1 - rho
    return 1.0  # for higher scores, no adjustment
```

---

## 3. FIFA 2026 Bracket Construction  🟠 HIGH

### Finding
The bracket construction in `run_single_tournament_py()` does not correctly separate group winners from third-placed teams, and does not follow the official FIFA 2026 schedule.

### Code
```python
# monte_carlo.py:266-298
winners = qualified[0::2]  # <-- BUG: takes every other team
# ...
for i in range(min(len(winners), len(all_runners))):
    bracket_r32[2 * i] = winners[i]
    bracket_r32[2 * i + 1] = all_runners[i]
```

### Bug
`qualified` = [W₀, RU₀, W₁, RU₁, W₂, RU₂, ..., T₀, T₁, T₂, ..., T₇]
`qualified[0::2]` = [W₀, W₁, W₂, ..., T₀, T₂, T₄, T₆]

This interleaves third-placed teams as "winners" and excludes some actual group winners from the top-seeded bracket positions.

### Official FIFA 2026 Format
The Round of 32 has a predetermined template depending on which groups the best third-placed teams come from (FIFA has 4-5 pre-defined templates). The bracket is NOT a simple linear interleave.

### Impact
- Incorrect bracket pairings produce biased tournament advancement probabilities
- Some group winners face stronger opponents than intended
- Some third-placed teams are incorrectly seeded as winners

### Recommended Fix
1. Separate group winners explicitly (not via qualified[0::2])
2. Implement one of the 4-5 official FIFA third-placed pairing templates
3. Add positional tracking to confirm correct bracket construction

---

## 4. Knockout Draw Handling  🟡 MEDIUM

### Finding
Knockout matches that would end in a draw after 90+120 minutes are not distinguished from home wins.

### Code
```python
# monte_carlo.py:191-195
ga, gb = simulate_knockout_match(strengths[ti], strengths[tj])
if ga >= gb:
    winners[i // 2] = ti  # <-- draw goes to team A
else:
    winners[i // 2] = tj
```

### Issues
1. **No extra time simulation**: Draws after 90 minutes should go to extra time (30 min, lower expected goals).
2. **No penalties**: Extra time draws should go to penalties.

### Impact
- Biased toward team A (listed first) in drawn matches
- For evenly matched teams, Poisson draws occur ~25-30% of the time — all go to team A
- This inflates advancement probability for the first-listed team

### Recommended Fix
```python
if ga > gb:
    winners[i // 2] = ti
elif gb > ga:
    winners[i // 2] = tj
else:
    # Extra time: simulate with lower lambdas
    eta_a = max(0.05, np.exp(sa - sb) * 0.3)
    eta_b = max(0.05, np.exp(sb - sa) * 0.3)
    eta_ga = np.random.poisson(eta_a)
    eta_gb = np.random.poisson(eta_b)
    if eta_ga > eta_gb:
        winners[i // 2] = ti
    elif eta_gb > eta_ga:
        winners[i // 2] = tj
    else:
        # Penalties: 50/50
        winners[i // 2] = ti if np.random.random() < 0.5 else tj
```

---

## 5. Confidence Index Validity  🟠 HIGH

### Finding
The Confidence Index is dominated by IGF (typically 59-85% of the score) due to a scale mismatch, making the 50/50 Elo-IGF weighting meaningless.

### Code
```python
# match_prediction.py:349-353
elo_confidence = min(100, elo_diff / 20)        # e.g., 1400/20 = 70
igf_confidence = min(100, igf_diff * 100)        # e.g., 90*100 = 9000 → capped at 100
```

### Measured Values
| Match | Elo diff | elo_conf | IGF diff | igf_conf | Total | IGF % |
|-------|----------|----------|----------|----------|-------|-------|
| Brazil vs Japan | 600 | 30.0 | 55 | 100 | 65.0 | 77% |
| Argentina vs Costa Rica | 400 | 20.0 | 40 | 100 | 60.0 | 83% |
| Germany vs Japan | 350 | 17.5 | 35 | 100 | 58.8 | 85% |

### Root Cause
`igf_diff * 100` assumes IGF is on a 0-1 scale, but it's now 0-100. The multiplier should be 1.0 (or the scale should be consistent).

### Impact
- The Confidence Index is essentially a capped IGF differential index
- Elo contributes almost nothing for most matches
- The confidence level classification (Muy Alta/Alta/Media/Baja) is unreliable

### Required Fix
Either:
- Scale IGF back to 0-1 for confidence computation: `igf_diff / 100.0`
- Or normalize both components to comparable ranges: `min(100, elo_diff / 20)` + `igf_diff / 100 * 50`

---

## 6. IGF / Expected Goals Coherence  🔴 CRITICAL

### Finding
The IGF score is used in TWO different scaling contexts, producing completely inconsistent expected goals between engines.

### Code Comparison

| Engine | Strength Formula | λ for Brazil(95) vs Saudi(30) |
|--------|-----------------|-------------------------------|
| Match prediction | `exp(igf_home - igf_away)` | exp(95-30) = **1.22e+39** |
| Monte Carlo | `exp(igf_home/50 - igf_away/50)` | exp(1.9-0.6) = **3.67** |
| Match service | `min(1.0, max(0.0, (elo-1300)/800))` | exp(...) using 0-1 scale (third scale!) |

Additionally, `MatchService._load_team_entity()` computes the IGF strength differently:

```python
# match_service.py:62
igf_strength = min(1.0, max(0.0, (elo_score - 1300) / 800))
```

This is a LINEAR mapping from Elo to [0, 1], NOT using the actual IGF engine at all. So the IGF score stored in `TeamEntity.igf_score` is actually just a linear Elo projection, not the 8-factor composite strength index.

### Triple Inconsistency
1. Match prediction engine: IGF 0-100 → exp(IGF) → λ = 10^30+
2. Monte Carlo engine: IGF/50 → exp(IGF/50) → λ = 0.1-7.4
3. Match service: IGF = (elo-1300)/800 → exp(0-1) → λ = 0.4-2.7

### Impact
- Each component of the system produces different predictions for the same match
- The "IGF score" stored in TeamEntity has different semantics depending on which service sets it
- The calibration engine tests using hardcoded igf values (0-1 scale) don't match production behavior (0-100 scale)

---

## 7. IGF Min-Max Scaling Bias  🟡 MEDIUM

### Finding
The IGF engine uses min-max normalization to map raw scores to 0-100, which introduces dataset-composition dependency.

### Code
```python
# igf.py:104-109
min_raw = df["igf_score_raw"].min()
max_raw = df["igf_score_raw"].max()
df["igf_score"] = ((df["igf_score_raw"] - min_raw) / (max_raw - min_raw)) * 100
```

### Issues
1. **Relative, not absolute**: A team scoring IGF=50 is just the median of the current dataset, not a universally "average" team.
2. **Range compression**: If the dataset has 48 evenly-matched World Cup teams, the range is ~0.3 (raw 0.05 to 0.35). Adding San Marino (raw 0.01) would expand the range to ~0.34, compressing all existing scores.
3. **Non-portable**: IGF scores from different ranking runs are not comparable unless computed on exactly the same team set.

### Example (48 simulated WC teams)
- Raw score range: [0.045, 0.334] — span of 0.289
- After min-max: [0.0, 100.0] — always the full range
- A team with raw=0.19 scores 50, but that's just the dataset median

### Recommended Fix
Use a fixed reference scale. For example:
- Map Elo 1300→0, 2100→100 directly
- Or use z-score standardization against a fixed historical mean/std
- This preserves comparability across ranking updates

---

## Summary of Findings

| # | Issue | Severity | Component | Impact |
|---|-------|----------|-----------|--------|
| 1 | Poisson lambda uses raw IGF 0-100 without scaling | 🔴 CRITICAL | match_prediction.py | All predictions meaningless |
| 2 | Dixon-Coles simplified — flat multipliers, no λ/μ dependence | 🟠 HIGH | match_prediction.py | Quantitatively imprecise |
| 3 | Bracket construction uses qualified[0::2], not explicit winners | 🟠 HIGH | monte_carlo.py | Incorrect pairings |
| 4 | No extra time/penalties in knockout draws | 🟡 MEDIUM | monte_carlo.py | Team A bias in draws |
| 5 | Confidence Index dominated by IGF (77-85%) | 🟠 HIGH | match_prediction.py | Unreliable confidence |
| 6 | Triple IGF scaling inconsistency (0-100, /50, Elo-linear) | 🔴 CRITICAL | cross-component | System incoherence |
| 7 | Min-max scaling is dataset-dependent | 🟡 MEDIUM | igf.py | Non-portable scores |

### Priority Order for Fixes
1. **#1 & #6** — Poisson lambda: divide IGF by 50 in match_prediction.py (fixes both)
2. **#5** — Confidence Index: fix IGF multiplier (100 → 1 or /100)
3. **#4** — Knockout draws: add extra time + penalties
4. **#3** — Bracket: use explicit winner array
5. **#2** — Dixon-Coles: add proper tau function
6. **#7** — IGF scaling: use fixed reference scale
