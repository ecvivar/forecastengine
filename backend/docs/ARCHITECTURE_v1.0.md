# ForecastEngine2026 v1.0 — Architecture Snapshot

## Domain Layer

| File | Key Types |
|------|-----------|
| `domain/entities.py` | TeamEntity, TeamStrength, MatchEntity, MatchPredictionResult, PredictionConfig, SimulationConfig, TournamentResult, TournamentUncertainty, ScenarioConfig, BracketNode |

## Engine Layer

| File | Key Classes | Purpose |
|------|-------------|---------|
| `engine/match_prediction.py` | `MatchPredictionEngine` | Hybrid Elo + xG prediction with Dixon-Coles, Bayesian prior, confidence, betting markets |
| `engine/meta_ensemble.py` | `MetaPredictionEngine` | 4-model ensemble (Poisson-xG, Bayesian Elo, Dixon-Coles, Strength Diff) |
| `engine/dynamic_elo.py` | `DynamicEloEngine` | Glicko-style rating with RD, volatility |
| `engine/monte_carlo.py` | `MonteCarloEngine` | 48-team, 12-group tournament simulation with Numba JIT |
| `engine/igf.py` | `IGFEngine` | Integrated Grading Formula (Elo + xG + FIFA composite) |
| `engine/calibration.py` | `Calibrator` | Platt scaling for probability calibration |
| `engine/calibration_refinement.py` | `ProbabilisticCalibrator` | Temperature, Platt, Isotonic + bias reduction |
| `engine/explainability.py` | `ExplainabilityEngine` | Per-signal ablation analysis |
| `engine/tournament_explainability.py` | `TournamentExplainabilityEngine` | Tournament-level driver attribution |

## Validation Layer

| File | Key Purpose |
|------|-------------|
| `validation/backtesting.py` | Tournament backtesting |
| `validation/calibration_metrics.py` | Accuracy, Brier, LogLoss, RPS, ECE |
| `validation/ci_calibration.py` | Confidence interval calibration |
| `validation/ci_width_analysis.py` | CI width optimization |
| `validation/conformal.py` | Conformal prediction methods |
| `validation/coverage_validation.py` | Coverage rate validation |
| `validation/elite_score.py` | Elite readiness scoring |
| `validation/elo_pareto.py` | Elo weight optimization (Pareto) |
| `validation/elo_sensitivity.py` | Elo parameter sensitivity |
| `validation/ensemble_dominance.py` | Model dominance analysis |
| `validation/mc_noise_analysis.py` | Monte Carlo noise characterization |
| `validation/pearson_audit.py` | Pearson/Spearman correlation audit |
| `validation/probability_calibration.py` | Temperature + Platt calibration |
| `validation/regional_calibration.py` | Region-independent calibration |
| `validation/reliability.py` | Reliability diagram + ECE |
| `validation/sensitivity_decomposition.py` | Sensitivity attribution |
| `validation/stress_attribution.py` | Stress test attribution |
| `validation/temporal_validation.py` | Time-series validation |
| `validation/tournament_forecasting.py` | Tournament forecast validation |
| `validation/uncertainty_consistency.py` | Uncertainty metric consistency |
| `validation/weight_optimizer.py` | Ensemble weight optimization |

## Monitoring Layer

| File | Key Classes | Purpose |
|------|-------------|---------|
| `monitoring/calibration_tracker.py` | `CalibrationTracker` | Live accuracy/brier/ece/coverage per window |
| `monitoring/drift_detector.py` | `DriftDetector` | PSI, KL, JS divergence on Elo/prediction/uncertainty |
| `monitoring/dashboard_metrics.py` | `DashboardMetrics` | JSON-ready dashboard data |
| `monitoring/reality_tracker.py` | `RealityTracker` | Post-match surprise/upset analysis |
| `monitoring/recalibration_simulator.py` | `RecalibrationSimulator` | Recalibration strategy benchmarking |

## Audit Layer

| File | Key Classes | Purpose |
|------|-------------|---------|
| `audit/prediction_audit.py` | `PredictionAudit` | Full prediction log with context |

## Versioning Layer

| File | Key Classes | Purpose |
|------|-------------|---------|
| `versioning/model_registry.py` | `ModelRegistry` | Sprint/config/calibration/ensemble versioning |

## API Layer (50 endpoints)

| Router | Prefix | Endpoints |
|--------|--------|-----------|
| health | `/health` | 5 |
| teams | `/api/v1/teams` | 5 |
| matches | `/api/v1/matches` | 4 |
| groups | `/api/v1/groups` | 2 |
| predictions | `/api/v1/predictions` | 2 |
| rankings | `/api/v1/rankings` | 3 |
| simulations | `/api/v1/simulations` | 4 |
| calibration | `/api/v1/calibration` | 5 |
| calibration/refinement | `/api/v1/calibration/refinement` | 2 |
| analysis | `/api/v1/analysis` | 5 |
| dashboard | `/api/v1/dashboard` | 2 |
| comparison | `/api/v1/comparison` | 1 |
| competitions | `/api/v1/competitions` | 1 |
| export | `/api/v1/export` | 7 |
| scenarios | `/api/v1/scenarios` | 1 |
| explain | `/api/v1/matches/explain` | 1 |

## Data Flow

```
TeamEntity
  │
  ├─→ MatchPredictionEngine
  │     ├─→ compute_team_strength() → TeamStrength
  │     ├─→ _predict_dixon_coles() → DC probabilities
  │     ├─→ _bayesian_update() → calibrated probs
  │     ├─→ _compute_confidence() → ConfidenceLevel
  │     ├─→ _compute_surprise_risk() → surprise
  │     └─→ betting markets (BTTS, O/U, CS)
  │
  ├─→ MetaPredictionEngine
  │     ├─→ Model A: Poisson-xG (no prior, no DC)
  │     ├─→ Model B: Bayesian Elo (pure prior)
  │     ├─→ Model C: Dixon-Coles (full)
  │     ├─→ Model D: Strength Differential
  │     └─→ weighted average → final probs
  │
  ├─→ MonteCarloEngine
  │     ├─→ simulate_group_stage_numba() (48 teams, 12 groups)
  │     ├─→ rank_group_fifa() (tiebreakers)
  │     ├─→ select_best_third_numba() (best 8 third-placed)
  │     ├─→ run_knockout_round() × 5 (R32→R16→QF→SF→Final)
  │     └─→ TournamentResult[] (stage probabilities)
  │
  ├─→ Calibration Layer
  │     ├─→ Temperature scaling
  │     ├─→ Platt scaling
  │     └─→ Regional calibration
  │
  ├─→ Monitoring Layer
  │     ├─→ CalibrationTracker (per-window metrics)
  │     ├─→ DriftDetector (distribution shifts)
  │     └─→ RealityTracker (post-match analysis)
  │
  └─→ Audit Layer
        ├─→ PredictionAudit (every prediction logged)
        └─→ ModelRegistry (version control)
```
