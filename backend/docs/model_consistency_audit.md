# Model Consistency Audit Report

**Date:** 2026-06-19
**Scope:** `match_prediction.py`, `monte_carlo.py`, `explainability.py`, `tournament_explainability.py`, `entities.py` (PredictionConfig), `weight_optimizer.py`

---

## Executive Summary

The engine suffers from **two fundamental model mismatches** and **one optimizer defect**:

1. **Match-level vs. Tournament model mismatch** — the Poisson formula used at match level (`λ = μ · attack · defense · (1+HA)`) is structurally different from the tournament simulator (`λ = exp(sᵢ − sⱼ)`). They are not mathematically equivalent.
2. **Weights are decorative at match level** — the four signal weights (`elo_weight`, `xg_attack_weight`, `xg_defense_weight`, `fifa_weight`) only affect `overall_strength`, which is **never used** by `predict_full()`. They only propagate to Monte Carlo.
3. **WeightOptimizer is structurally broken** — it grid-searches over the four weights but evaluates using `predict_full()`, which ignores every weight. All weight combinations yield identical log loss.

---

## Pregunta 1 — Variables Affecting Each Function

### 1.1 `_compute_team_strength(team)` → `match_prediction.py:165-207`

| Variable | Use | Mechanism | Line |
|----------|-----|-----------|------|
| `team.elo_score` | `elo_norm = elo_score / 1500.0` | Scalar division (no cap) | 172 |
| `team.xg_for` | `attack_xg = xg_for / 1.5`, clamped to [0.3, 3.0] | Division by league-average xG (1.5) | 175-179 |
| `team.xg_against` | `defense_xg = 1.5 / xg_against`, clamped to [0.3, 3.0] | Inverse ratio | 181-185 |
| `team.fifa_rank` | `fifa_norm = max(0.3, min(3.0, 100.0 / rank))` | Inverse rank capped at 0.3–3.0 | 188-189 |
| `config.*_weight` | `overall = (w.elo*elo_norm + w.xg_atk*attack_xg + w.xg_def*defense_xg + w.fifa*fifa_norm) / total_w` | Weighted average → `overall_strength` | 193-201 |

**Returns** `TeamStrength(attack_strength=attack_xg, defense_strength=defense_xg, overall_strength=overall)` (lines 203-206). Note: `attack_strength` and `defense_strength` are **independent of all weights** and of `elo_score`/`fifa_rank`.

---

### 1.2 `_predict_dixon_coles()` → `match_prediction.py:272-284`

Calls `_compute_poisson_matrix()` (line 213-270):

| Variable | Use | Mechanism | Line |
|----------|-----|-----------|------|
| `config.league_avg_goals` (μ) | `λ_home = μ · attack_home · defense_away · (1+HA)` | Multiplicative base rate | 223, 226 |
| `home_s.attack_strength` | Factor in λ_home | From xg_for only | 226 |
| `away_s.defense_strength` | Factor in λ_home | From xg_against only | 226 |
| `config.home_advantage` (HA) | Multiplier on λ_home: `(1.0 + ha)` | 0.08 by default | 224, 226 |
| `away_s.attack_strength` | Factor in λ_away | From xg_for only | 227 |
| `home_s.defense_strength` | Factor in λ_away | From xg_against only | 227 |
| `config.max_goals` | Upper bound of Poisson summation | Truncates the score grid | 232 |
| `config.dixon_coles_tau` (ρ) | Adjusts 0-0, 0-1, 1-0, 1-1 probabilities | Multiplicative correction with renormalization | 280, 307-340 |

**Variables NOT used:** `overall_strength`, `elo_score`, `fifa_rank`, any signal weight.

---

### 1.3 `predict_full()` → `match_prediction.py:58-131`

Orchestrates the full match pipeline. Here is every variable path:

```
home_team / away_team (TeamEntity)
├── elo_score ──────────────→ _bayesian_update() [line 82-83] ──→ prior via Elo diff
│                             → _compute_confidence() [line 395] → confidence index
├── xg_for ─────────────────→ _compute_team_strength() [line 71-72]
│                             → TeamStrength.attack_strength ──→ Poisson λ [line 226-227]
│                                                               → confidence [line 399]
├── xg_against ────────────→ _compute_team_strength()
│                             → TeamStrength.defense_strength ──→ Poisson λ [line 226-227]
│                                                               → confidence [line 399]
├── fifa_rank ─────────────→ _compute_team_strength()
│                             → TeamStrength.overall_strength ──→ (NOT USED by predict_full)
└── id, name ──────────────→ Metadata only

config (PredictionConfig)
├── league_avg_goals ──────→ Poisson μ [line 223]
├── home_advantage ────────→ λ_home multiplier [line 224, 226]
├── dixon_coles_tau ───────→ DC correction [line 280]
├── bayesian_prior_strength → Bayesian update weight [line 370]
├── max_goals ─────────────→ Poisson truncation [line 232]
└── calibration_adjustments → Post-hoc adjustment [line 91-94]
```

**Critical:** `overall_strength` is computed but **never referenced** in `predict_full()`. Attack/defense strengths come directly from xG values, bypassing all weights.

---

### 1.4 `overall_strength` attribute → `entities.py:139`

Computed at `match_prediction.py:193-201`:

```
overall = (w_elo·elo_norm + w_xg_atk·attack_xg + w_xg_def·defense_xg + w_fifa·fifa_norm)
          / (w_elo + w_xg_atk + w_xg_def + w_fifa)
```

**Used by:**
- `MonteCarloEngine._compute_strength_array()` → `monte_carlo.py:376`
- `TournamentExplainabilityEngine.explain_team()` → `tournament_explainability.py:52-53`
- `ExplainabilityEngine.explain()` → does NOT use overall_strength (uses predict_full)

**NOT used by:**
- `predict_full()` (match level)
- `predict_poisson()` (match level)
- `_predict_dixon_coles()`
- `_compute_poisson_matrix()`

---

### 1.5 `MonteCarloEngine.run()` → `monte_carlo.py:380-404`

```
teams (list[TeamEntity])
└── elo_score, xg_for, xg_against, fifa_rank ──→ _compute_strength_array() [line 390, 373-378]
                                                  → overall_strength ──→ np.ndarray strengths

strengths array passed to:
├── simulate_group_stage_numba() [line 243]
│   └── λ_i = max(0.1, exp(sᵢ − sⱼ))   [line 57]
│   └── λ_j = max(0.1, exp(sⱼ − sᵢ))   [line 58]
└── run_knockout_round() [lines 331, 337, 343, 349, 356]
    └── simulate_knockout_match() [line 217]
        └── λ_a = max(0.1, exp(sₐ − s_b))  [line 140]
        └── λ_b = max(0.1, exp(s_b − sₐ))  [line 141]
        └── Extra time: 0.33× intensity    [lines 150-151]
        └── Penalties: 50/50               [line 160]
```

**Variables not used in Monte Carlo:** `home_advantage`, `dixon_coles_tau`, `league_avg_goals`, `bayesian_prior_strength`, `max_goals`, `calibration_adjustments`, individual attack/defense strengths.

---

## Pregunta 2 — Match-Level vs Tournament Variable Coverage

### Variables affecting matches but NOT tournaments

| Variable | Match | Tournament | Mechanism |
|----------|-------|------------|-----------|
| `config.home_advantage` | Yes (λ_home × 1.08) | **No** | HA does not appear in any Monte Carlo code |
| `config.dixon_coles_tau` | Yes (DC correction) | **No** | DC is never applied in Monte Carlo |
| `config.league_avg_goals` | Yes (Poisson μ) | **No** | MC uses `exp(sᵢ−sⱼ)`, not μ |
| `config.bayesian_prior_strength` | Yes (Bayesian update) | **No** | MC has no Bayesian component |
| `config.max_goals` | Yes (truncation) | **No** | MC is unbounded Poisson |
| `config.calibration_adjustments` | Yes (post-hoc) | **No** | MC has no calibration step |

### Variables affecting tournaments but NOT match-level predictions

| Variable | Match | Tournament | Mechanism |
|----------|-------|------------|-----------|
| `elo_weight` (the weight parameter) | **No** | Yes | Only changes `overall_strength` composition; `predict_full` ignores it |
| `xg_attack_weight` | **No** | Yes | Same — decorative in `predict_full` |
| `xg_defense_weight` | **No** | Yes | Same — decorative in `predict_full` |
| `fifa_weight` | **No** | Yes | Same — decorative in `predict_full` |

**Important distinction:** The raw signal *values* (e.g., `team.elo_score`) affect both domains, but the signal *weights* (`config.elo_weight`, etc.) affect only Monte Carlo. The raw `fifa_rank` is the only raw signal that affects only Monte Carlo (it never enters any match-level equation).

---

## Pregunta 3 — Decorative Variables (Zero Effect on Output)

### 3.1 Decorative in match-level prediction

| Variable | Why decorative |
|----------|---------------|
| `elo_weight` | Only used in `overall_strength` formula (line 194); `overall_strength` is never read by any match-level function |
| `xg_attack_weight` | Same — only weights `overall_strength`; `attack_strength` itself is computed from raw `xg_for` (line 176) without weighting |
| `xg_defense_weight` | Same — only weights `overall_strength`; `defense_strength` comes from raw `xg_against` (line 182) |
| `fifa_weight` | Same — only weights `overall_strength`; FIFA rank has no other match-level path |
| `team.fifa_rank` | Only flows into `fifa_norm` → `overall_strength`; this path is never used by match prediction functions |

### 3.2 Decorative in tournament simulation

| Variable | Why decorative |
|----------|---------------|
| `config.home_advantage` | MC uses symmetric `exp(sᵢ−sⱼ)` with no HA factor |
| `config.dixon_coles_tau` | MC has no DC correction; raw Poisson is used directly |
| `config.league_avg_goals` | MC goal rate is `exp(sᵢ−sⱼ)`, not `μ·attack·defense` |
| `config.bayesian_prior_strength` | MC has no Bayesian update step |
| `config.max_goals` | MC uses unbounded `np.random.poisson()` |
| `TeamStrength.attack_strength` | MC uses only `overall_strength`, ignores attack/defense split |
| `TeamStrength.defense_strength` | Same |

### 3.3 The WeightOptimizer is structurally broken

`weight_optimizer.py:79-108` grids over `elo_weight`, `xg_attack_weight`, `xg_defense_weight`, `fifa_weight`, then calls `engine.predict_full()` (line 95). Since **none of the four weights affect `predict_full()` output**, every valid weight combination produces **identical Brier and log-loss scores**. The optimizer will return whichever combination is evaluated first.

**Evidence:**
- `predict_full()` only uses `team.elo_score` (raw), `team.xg_for`, `team.xg_against` (raw), `config.home_advantage`, `config.dixon_coles_tau`, `config.league_avg_goals`, `config.bayesian_prior_strength`, `config.max_goals`.
- It never reads `config.elo_weight`, `config.xg_attack_weight`, `config.xg_defense_weight`, or `config.fifa_weight`.
- The `overall_strength` field that uses these weights is computed but never consumed by `predict_full()`.

**Fix required:** The optimizer must either (a) evaluate tournament-level metrics from Monte Carlo, or (b) make `predict_full()` actually use the weighted components (e.g., use a weighted attack/defense formulation).

---

## Comprehensive Variable Table

| Variable | Match-Level | Tournament | Explainability | Optimizer |
|----------|-------------|------------|----------------|-----------|
| **Elo** | **Yes** — via `_bayesian_update()` (lines 358-359) as Bayesian prior (Elo diff → logistic expected score) AND via `_compute_confidence()` (line 395) as `abs(elo_diff)/8.0` weighted at 60% | **Yes** — via `elo_norm = elo_score/1500.0` weighted by `elo_weight` into `overall_strength` (line 194) | **Yes** — Match: neutralizes Bayesian prior strength to 0 (explainability.py:97). Tournament: decomposes `elo_norm` × weight / total_w as pct contribution (tournament_explainability.py:79) | **Yes, but broken** — `elo_score` affects match output, but `elo_weight` (the optimizer's parameter) does NOT affect `predict_full()` |
| **xG Attack** | **Yes** — via `attack_xg = xg_for/1.5` clamped → `TeamStrength.attack_strength` → Poisson λ_home (line 226) and λ_away (line 227) multiplier | **Yes** — via `attack_xg` × `xg_attack_weight` → `overall_strength` (line 195) | **Yes** — Match: sets `xg_for=None` causing fallback to 1.0 (explainability.py:103-108). Tournament: `attack_xg` × weight / total_w (tournament_explainability.py:80) | **Yes, but broken** — raw `xg_for` affects match output, but `xg_attack_weight` does NOT affect `predict_full()` |
| **xG Defense** | **Yes** — via `defense_xg = 1.5/xg_against` clamped → `TeamStrength.defense_strength` → Poisson λ_home (line 226) and λ_away (line 227) multiplier | **Yes** — via `defense_xg` × `xg_defense_weight` → `overall_strength` (line 196) | **Yes** — Match: sets `xg_against=None` causing fallback to 1.0 (explainability.py:111-116). Tournament: `defense_xg` × weight / total_w (tournament_explainability.py:81) | **Yes, but broken** — raw `xg_against` affects match output, but `xg_defense_weight` does NOT affect `predict_full()` |
| **FIFA** | **No** — `fifa_rank` flows only into `fifa_norm` → `overall_strength` (line 189); `overall_strength` is never read by any match-level function. The explainability engine explicitly notes this: "FIFA has zero effect on predict_full (only MC)" (explainability.py:119) | **Yes** — via `fifa_norm = 100/rank` clamped, × `fifa_weight` → `overall_strength` (line 197) | **Yes** — Match: computes delta by setting rank to 100, yields 0.0 contribution (explainability.py:121-126). Tournament: `fifa_norm` × weight / total_w (tournament_explainability.py:82) | **No** — FIFA rank and `fifa_weight` have zero effect on `predict_full()`. The optimizer can never learn an optimal FIFA weight. |
| **Home Adv** | **Yes** — `config.home_advantage` multiplies λ_home by `(1.0 + HA)` (line 226), default +8% | **No** — Monte Carlo uses symmetric `exp(sᵢ−sⱼ)` with no home-side boost; knockout matches have no HA (monte_carlo.py:140-141) | **Yes** — Match: runs prediction with `home_advantage=False`, measures delta (explainability.py:129-130). Tournament: explicitly excluded from `overall_strength` (tournament_explainability.py:97-98) | **Yes** — `config.home_advantage` directly changes λ_home, so it affects `predict_full()` output. However, it is NOT part of the grid search parameter space (weight_optimizer.py:29-32) |
| **Dixon-Coles** | **Yes** — `config.dixon_coles_tau` (ρ=0.1) adjusts 0-0↓, 0-1↑, 1-0↑, 1-1↓ probabilities with renormalization (lines 314-327) | **No** — Monte Carlo Poisson is raw; no DC correction applied | **Yes** — Match: sets `dixon_coles_tau=0.0`, measures delta (explainability.py:133-137). Tournament: no role in overall_strength | **Yes** — τ directly changes score probabilities → affects `predict_full()` log loss. Not in grid search. |

---

## Structural Model Mismatch

The match-level and tournament engines use **different mathematical models** for goal generation:

| Aspect | Match-Level (`_compute_poisson_matrix`) | Tournament (`simulate_group_stage_numba`) |
|--------|----------------------------------------|-------------------------------------------|
| Formula | λ_home = μ · attack_home · defense_away · (1+HA) | λ_i = exp(sᵢ − sⱼ) |
| | λ_away = μ · attack_away · defense_home | λ_j = exp(sⱼ − sᵢ) |
| Base rate | μ = config.league_avg_goals (default 1.25) | Implicitly 1.0 (exp(0) = 1) |
| Team strength | 2-vector (attack, defense) | 1 scalar (overall) |
| Home advantage | Explicit (1+HA) multiplier | None |
| Correction | Dixon-Coles (τ) for low scores | Raw Poisson |
| Under 0.1 clamp | Both λ clamped ≥ 0.1 | Both λ clamped ≥ 0.1 |

**These are not mathematically equivalent.** There is no set of weights that makes `overall_strength` (a scalar) reproduce the behavior of the 2-vector attack/defense model. A team with strong attack and weak defense will have identical tournament behavior as a team with balanced medium strength, but very different match-level predictions.

---

## Per-Function Variable Trace

### `_compute_team_strength(team)` — Variables read

```
team.elo_score     → elo_norm = elo_score/1500    [line 172]
team.xg_for        → attack_xg = xg_for/1.5        [line 176]
team.xg_against    → defense_xg = 1.5/xg_against   [line 182]
team.fifa_rank     → fifa_norm = 100/rank          [line 189]
config.elo_weight           → overall_strength numerator  [line 194]
config.xg_attack_weight     → overall_strength numerator  [line 195]
config.xg_defense_weight    → overall_strength numerator  [line 196]
config.fifa_weight          → overall_strength numerator  [line 197]
```

### `_compute_poisson_matrix(home_s, away_s, home_advantage)` — Variables read

```
config.league_avg_goals     → μ                     [line 223]
config.home_advantage       → HA (if home_advantage) [line 224]
home_s.attack_strength      → λ_home factor         [line 226]
away_s.defense_strength     → λ_home factor         [line 226]
away_s.attack_strength      → λ_away factor         [line 227]
home_s.defense_strength     → λ_away factor         [line 227]
config.max_goals            → truncation            [line 232]
```

### `_predict_dixon_coles(home_s, away_s, home_advantage)` — Additional variables

```
config.dixon_coles_tau      → ρ                     [line 280]
```

### `predict_full(home_team, away_team, home_advantage)` — All variables consumed

```
(Indirect) team.elo_score   → _bayesian_update      [lines 82-83]
(Indirect) team.xg_for      → attack_strength       [lines 71-72, 226-227]
(Indirect) team.xg_against  → defense_strength      [lines 71-72, 226-227]
(NOT used) team.fifa_rank   → only overall_strength (never read)
config.league_avg_goals     → μ                    [line 223]
config.home_advantage       → HA                   [lines 224, 226]
config.dixon_coles_tau      → τ                    [line 280]
config.bayesian_prior_strength → ψ (prior strength) [line 370]
config.max_goals            → truncation           [line 232]
config.calibration_adjustments → post-hoc adj      [lines 91-94]
```

### `MonteCarloEngine.run()` — All variables consumed

```
team.elo_score      → elo_norm → overall_strength  [line 376 via 194]
team.xg_for         → attack_xg → overall_strength [line 376 via 195]
team.xg_against     → defense_xg → overall_strength [line 376 via 196]
team.fifa_rank      → fifa_norm → overall_strength [line 376 via 197]
config.elo_weight, xg_attack_weight, xg_defense_weight, fifa_weight
                    → overall_strength weighting   [lines 194-197, called from 376]
```

**NOT consumed by Monte Carlo:** `home_advantage`, `dixon_coles_tau`, `league_avg_goals`, `bayesian_prior_strength`, `max_goals`, `calibration_adjustments`.

---

## Detailed Line-by-Line Trace for Key Paths

### Path: Elo → match prediction

```
TeamEntity.elo_score
├── _compute_team_strength() → elo_norm → overall_strength → (not used in match)
├── predict_full() → _bayesian_update()
│   └── elo_diff = elo_home - elo_away                            [line 358]
│   └── elo_expected_home = 1 / (1 + 10^(-elo_diff/400))          [line 359]
│   └── prior_home = elo_expected_home                             [line 361]
│   └── prior_away = 1 - prior_home - prior_draw                  [line 363]
│   └── updated = (ψ·prior + dc_prob) / (ψ + 1)                   [lines 372-374]
└── predict_full() → _compute_confidence()
    └── elo_diff = abs(elo_home - elo_away)                        [line 395]
    └── elo_conf = min(100, elo_diff / 8.0)                        [line 396]
    └── confidence = 0.6·elo_conf + 0.4·xg_conf                     [line 404]
```

### Path: xG → match prediction

```
TeamEntity.xg_for
├── _compute_team_strength() → attack_xg = xg_for/1.5              [line 176]
│   → TeamStrength.attack_strength → _compute_poisson_matrix()
│     λ_home = μ · attack_home · defense_away · (1+HA)            [line 226]
│     λ_away = μ · attack_away · defense_home                     [line 227]
│   → _compute_confidence()
│     xg_diff = |(atk_home - def_away) - (atk_away - def_home)|   [line 399]
│     xg_conf = min(100, xg_diff × 30)                             [line 402]

TeamEntity.xg_against
├── _compute_team_strength() → defense_xg = 1.5/xg_against         [line 182]
│   → TeamStrength.defense_strength (same path as above)
```

### Path: FIFA → (no match-level effect)

```
TeamEntity.fifa_rank
├── _compute_team_strength() → fifa_norm = 100/rank, clamped      [line 189]
│   → TeamStrength.overall_strength (NOT attack/defense)          [line 206]
│   → predict_full() → (overall_strength never accessed)
│   → MonteCarloEngine → _compute_strength_array() → overall_strength  [line 376]
```

### Path: Home advantage → only match level

```
config.home_advantage (default 0.08)
├── _compute_poisson_matrix()
│   └── ha = config.home_advantage if home_advantage else 0.0      [line 224]
│   └── λ_home = μ · attack_home · defense_away · (1.0 + ha)      [line 226]
├── MonteCarlo: (not used)
```

---

## Recommendations

1. **Unify the goal model:** Either make Monte Carlo use the same attack/defense Poisson formula as match-level, or make match-level use the scalar strength-difference model. The current dual-model architecture guarantees inconsistent predictions.

2. **Make `predict_full()` weight-aware:** If the weights are meant to tune signal importance at match level, `predict_full()` must actually use them — e.g., by computing weighted attack/defense composites rather than raw xG values.

3. **Fix the WeightOptimizer:** It currently measures `predict_full()` output, which is invariant to the grid parameters. Either (a) re-target to Monte Carlo tournament metrics, (b) make `predict_full()` weight-responsive, or (c) remove the optimizer as misleading.

4. **Add FIFA to match-level or remove it:** A signal that only affects `overall_strength` but never reaches match predictions creates a false sense of model sophistication. Either incorporate `fifa_rank` into the Poisson λ formula (e.g., as a scaling factor on λ) or remove it from the model entirely.

5. **Align explainability engines:** The match-level explainer computes FIFA contribution as 0 (correct), while tournament explainer shows it as non-zero. This is consistent per domain but will confuse users who see different FIFA importances for the same match in different reports.
