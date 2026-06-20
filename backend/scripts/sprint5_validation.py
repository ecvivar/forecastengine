"""
Sprint 5 — Main validation: runs all modules and collects metrics.
"""
import json, logging, os, sys, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np

from app.data.historical_matches import ALL_HISTORICAL_MATCHES
from app.domain.entities import PredictionConfig, ScenarioConfig, TeamEntity
from app.engine.match_prediction import MatchPredictionEngine
from app.engine.meta_ensemble import MetaPredictionEngine
from app.engine.dynamic_elo import DynamicEloEngine
from app.engine.sprint5_modules import (
    ExplainabilityEngineV2, ScenarioEngine, SharpnessMetrics, StressTester,
    TournamentUncertaintyEngine,
)
from app.engine.explainability import ExplainabilityEngine
from app.validation.backtesting import BacktestingEngine
from app.validation.calibration_metrics import CalibrationMetrics
from app.validation.probability_calibration import ProbabilityCalibrator

DOCS = os.path.join(os.path.dirname(__file__), "..", "docs")
os.makedirs(DOCS, exist_ok=True)
logging.basicConfig(level=logging.INFO)

config = PredictionConfig()
base_engine = MatchPredictionEngine(config=config)
metrics = CalibrationMetrics()
bt = BacktestingEngine(config=config)
meta = MetaPredictionEngine(config=config)

team_data = bt._extract_team_data(ALL_HISTORICAL_MATCHES)
team_entities = {name: bt._build_team_entity(name, d) for name, d in team_data.items()}

probs = []
outcomes = []

for m in ALL_HISTORICAL_MATCHES:
    home = team_entities.get(m.home_team)
    away = team_entities.get(m.away_team)
    if not home or not away:
        continue
    r = meta.predict(home, away)
    probs.append([r.home_win_prob, r.draw_prob, r.away_win_prob])
    if m.home_goals > m.away_goals:
        outcomes.append([1, 0, 0])
    elif m.home_goals == m.away_goals:
        outcomes.append([0, 1, 0])
    else:
        outcomes.append([0, 0, 1])

probs_arr = np.array(probs)
outcomes_arr = np.array(outcomes)

print("=== SPRINT 5 — ULTRA PRO VALIDATION ===\n")

# ── Ensemble metrics ──
brier_e = metrics.brier_score(probs_arr, outcomes_arr)
logloss_e = metrics.log_loss(probs_arr, outcomes_arr)
rps_e = metrics.ranked_probability_score(probs_arr, outcomes_arr)
ece_e, ece_bins = metrics.expected_calibration_error(probs_arr, outcomes_arr)
accuracy_e = float(np.mean(np.argmax(probs_arr, axis=1) == np.argmax(outcomes_arr, axis=1)))
print(f"Ensemble metrics:")
print(f"  Accuracy: {accuracy_e:.4f}")
print(f"  Brier:    {brier_e:.6f}")
print(f"  LogLoss:  {logloss_e:.6f}")
print(f"  RPS:      {rps_e:.6f}")
print(f"  ECE:      {ece_e:.6f}")

# ── Calibrate ensemble with Temperature ──
cal = ProbabilityCalibrator()
calibrated, temp_params = cal.temperature_scaling(probs_arr, outcomes_arr)
brier_c = metrics.brier_score(calibrated, outcomes_arr)
logloss_c = metrics.log_loss(calibrated, outcomes_arr)
rps_c = metrics.ranked_probability_score(calibrated, outcomes_arr)
ece_c, _ = metrics.expected_calibration_error(calibrated, outcomes_arr)
print(f"\nAfter Temperature Scaling (T={temp_params['T']}):")
print(f"  Brier:    {brier_c:.6f}  (delta={brier_c - brier_e:+.6f})")
print(f"  LogLoss:  {logloss_c:.6f}  (delta={logloss_c - logloss_e:+.6f})")
print(f"  RPS:      {rps_c:.6f}  (delta={rps_c - rps_e:+.6f})")
print(f"  ECE:      {ece_c:.6f}  (delta={ece_c - ece_e:+.6f})")

# ── Individual model contributions ──
sample_home = team_entities.get("Brazil")
sample_away = team_entities.get("Argentina")
if sample_home and sample_away:
    contribs = meta.individual_contributions(sample_home, sample_away)
    print(f"\nIndividual model contributions (Brazil vs Argentina):")
    for name, data in contribs.items():
        print(f"  {name}: weight={data['weight']:.4f}, "
              f"hw={data['home_win']:.4f}, d={data['draw']:.4f}, aw={data['away_win']:.4f}")

# ── Learn weights ──
match_pairs = []
for m in ALL_HISTORICAL_MATCHES:
    home = team_entities.get(m.home_team)
    away = team_entities.get(m.away_team)
    if not home or not away:
        continue
    if m.home_goals > m.away_goals:
        o = [1, 0, 0]
    elif m.home_goals == m.away_goals:
        o = [0, 1, 0]
    else:
        o = [0, 0, 1]
    match_pairs.append((home, away, np.array(o)))

print(f"\nLearning ensemble weights...")
weight_result = meta.learn_weights(match_pairs, n_trials=200)
print(f"  Best weights: {weight_result['best_weights']}")
print(f"  Best LogLoss: {weight_result['best_log_loss']:.6f}")

# ── Sharpness ──
sharp = SharpnessMetrics()
sharp_report = sharp.sharpness_score(probs_arr)
print(f"\nSharpness:")
for k, v in sharp_report.items():
    print(f"  {k}: {v}")

# ── Bootstrap CI example ──
if sample_home and sample_away:
    ci = meta.bootstrap_ci(sample_home, sample_away, n_resamples=500)
    print(f"\nBootstrap CI (Brazil vs Argentina):")
    for label, data in ci.items():
        print(f"  {label}: point={data['point']:.4f}, 90% CI=[{data['ci_lower']:.4f}, {data['ci_upper']:.4f}]")

# ── Scenario example ──
scenario_engine = ScenarioEngine(config=config)
if sample_home and sample_away:
    baseline = base_engine.predict_full(sample_home, sample_away)
    sc_injury = ScenarioConfig(injury=["Neymar"])
    injured = scenario_engine.apply(sample_home, sample_away, sc_injury)
    print(f"\nScenario — Brazil with injury:")
    print(f"  Baseline: hw={baseline.home_win_prob:.4f}, d={baseline.draw_prob:.4f}, aw={baseline.away_win_prob:.4f}")
    print(f"  Injury:   hw={injured.home_win_prob:.4f}, d={injured.draw_prob:.4f}, aw={injured.away_win_prob:.4f}")

# ── Stress test ──
stress = StressTester(config=config)
if sample_home and sample_away:
    stress_report = stress.run(sample_home, sample_away, n_scenarios=500)
    print(f"\nStress Test (Brazil vs Argentina, 500 scenarios):")
    for k, v in stress_report.items():
        print(f"  {k}: {v}")

# ── Dynamic Elo example ──
dyn_elo = DynamicEloEngine()
print(f"\nDynamic Elo — simulation:")
bra_id, arg_id = "Brazil", "Argentina"
dyn_elo.get_or_create(bra_id, 1850)
dyn_elo.get_or_create(arg_id, 1780)
fa = dyn_elo.update_rating(bra_id, arg_id, 2, 0)  # Brazil wins 2-0
fb = dyn_elo.update_rating(arg_id, bra_id, 0, 2)
print(f"  Brazil after win: rating={fa.rating}, RD={fa.rd}")
print(f"  Argentina after loss: rating={fb.rating}, RD={fb.rd}")

# ── Tournament Uncertainty example ──
tue = TournamentUncertaintyEngine()
tu = tue.compute("Brazil", 18200, 100000)
print(f"\nTournament Uncertainty (Brazil champion prob=18.2%):")
print(f"  variance={tu.variance}, std_dev={tu.std_dev}%, 90% CI=[{tu.ci_90[0]:.2f}%, {tu.ci_90[1]:.2f}%]")

# ── Explainability V2 ──
exp2 = ExplainabilityEngineV2(config=config)
if sample_home and sample_away:
    exp_match = exp2.explain_match(sample_home, sample_away)
    print(f"\nExplainability V2 — Match (Brazil vs Argentina):")
    for k, v in exp_match["drivers"].items():
        print(f"  {k}: {v}%")
    print(f"  Pred: {exp_match['prediction']}")

    # Tournament explainability
    teams = list(team_entities.values())
    champ_probs = {t.name: random.uniform(0.1, 18.0) for t in teams}
    exp_tourn = exp2.explain_tournament(teams, champ_probs, n_sims=5000)
    print(f"\nExplainability V2 — Tournament (average drivers):")
    for k, v in exp_tourn["average_drivers"].items():
        print(f"  {k}: {v}%")

# ── Save all data ──
data = {
    "ensemble": {
        "accuracy": round(accuracy_e, 6),
        "brier": round(brier_e, 6),
        "log_loss": round(logloss_e, 6),
        "rps": round(rps_e, 6),
        "ece": round(ece_e, 6),
    },
    "calibrated": {
        "brier": round(brier_c, 6),
        "log_loss": round(logloss_c, 6),
        "rps": round(rps_c, 6),
        "ece": round(ece_c, 6),
        "temperature": temp_params["T"],
    },
    "sharpness": sharp_report,
    "ensemble_weights": weight_result["best_weights"],
    "best_log_loss": weight_result["best_log_loss"],
    "individual_contributions": contribs if sample_home and sample_away else {},
    "bootstrap_ci": ci if sample_home and sample_away else {},
    "scenario": {
        "baseline_hw": round(baseline.home_win_prob, 4) if sample_home else None,
        "injury_hw": round(injured.home_win_prob, 4) if sample_home else None,
    },
    "stress_test": stress_report if sample_home else {},
    "dynamic_elo": {
        "bra_rating": fa.rating,
        "bra_rd": fa.rd,
        "arg_rating": fb.rating,
        "arg_rd": fb.rd,
    },
    "tournament_uncertainty": {
        "variance": tu.variance,
        "std_dev": tu.std_dev,
        "ci_90": tu.ci_90,
    },
    "explainability_match": exp_match if sample_home else {},
    "explainability_tournament_avg": exp_tourn["average_drivers"] if sample_home else {},
}

with open(os.path.join(DOCS, "sprint5_data.json"), "w") as f:
    json.dump(data, f, indent=2)
print(f"\nSaved to docs/sprint5_data.json")
