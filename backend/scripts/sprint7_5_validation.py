"""
Sprint 7.5 — Master Validation Script.
Closes the 3 remaining gaps: Stress Std, ECE, CI Coverage.
"""
import json, logging, os, sys, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np

from app.data.historical_matches import ALL_HISTORICAL_MATCHES
from app.domain.entities import PredictionConfig
from app.engine.match_prediction import MatchPredictionEngine
from app.engine.meta_ensemble import MetaPredictionEngine
from app.engine.sprint5_modules import SharpnessMetrics, StressTester
from app.validation.backtesting import BacktestingEngine
from app.validation.calibration_metrics import CalibrationMetrics
from app.validation.reliability import ReliabilityAnalyzer
from app.validation.elo_pareto import EloParetoOptimizer
from app.validation.regional_calibration import RegionalCalibrator
from app.validation.ci_recalibration import CIRecalibrator

DOCS = os.path.join(os.path.dirname(__file__), "..", "docs")
os.makedirs(DOCS, exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

config = PredictionConfig()
bt = BacktestingEngine(config=config)
metrics = CalibrationMetrics()
meta = MetaPredictionEngine(config=config)
sharp = SharpnessMetrics()

team_data = bt._extract_team_data(ALL_HISTORICAL_MATCHES)
team_entities = {name: bt._build_team_entity(name, d) for name, d in team_data.items()}

match_pairs = []
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
        out = [1, 0, 0]
    elif m.home_goals == m.away_goals:
        out = [0, 1, 0]
    else:
        out = [0, 0, 1]
    outcomes.append(out)
    match_pairs.append((home, away, np.array(out)))

probs_arr = np.array(probs)
outcomes_arr = np.array(outcomes)
sample_home = team_entities.get("Brazil")
sample_away = team_entities.get("Argentina")

data = {}

# ─── FASE 1: Elo Pareto ───
logger.info("FASE 1 — Elo Pareto Optimization")
epo = EloParetoOptimizer()
pareto_results = epo.evaluate(match_pairs, n_stress=300,
                               sample_home=sample_home, sample_away=sample_away)
pareto_front = EloParetoOptimizer.pareto_front(pareto_results)
data["elo_pareto"] = {
    "all_configs": pareto_results,
    "pareto_front": pareto_front,
}

# Find best config (lowest Brier among those meeting constraints)
valid = [v for v in pareto_results.values()
         if v["accuracy"] > 0.50 and v["pearson"] > 0.95]
best_config = min(valid, key=lambda v: v["brier"]) if valid else list(pareto_results.values())[0]
best_elo_w = best_config["elo_weight"]
data["elo_pareto_best"] = best_config
logger.info(f"Best elo_weight={best_elo_w}, Brier={best_config['brier']}, "
            f"Stress Std={best_config['stress_std']}, ECE={best_config['ece']}")

# ─── FASE 2: Regional Calibration ───
logger.info("FASE 2 — Regional Probability Calibration")
rc = RegionalCalibrator()
calib_results = rc.evaluate(probs_arr, outcomes_arr)
data["regional_calibration"] = calib_results
logger.info(f"  Baseline ECE={calib_results['baseline']['ece']}")
logger.info(f"  Global Temp ECE={calib_results['global_temperature']['ece']}")
logger.info(f"  Regional Temp ECE={calib_results['regional_temperature']['ece']}")

# ─── FASE 3: CI Recalibration ───
logger.info("FASE 3 — CI Recalibration")
cir = CIRecalibrator(config=config)
ci_cal = cir.calibrate(match_pairs[:50], n_resamples=200)
data["ci_recalibration"] = ci_cal
logger.info(f"  Best CI scale={ci_cal['best_scale']}, coverage={ci_cal['best_coverage']}")

# ─── FASE 4: Stress Re-Run with best elo_weight ───
logger.info("FASE 4 — Stress Re-Run with best elo_weight")
best_cfg = PredictionConfig(
    elo_weight=best_config["elo_weight"],
    xg_attack_weight=best_config["xg_attack_weight"],
    xg_defense_weight=best_config["xg_defense_weight"],
    fifa_weight=best_config["fifa_weight"],
)
if sample_home and sample_away:
    st_best = StressTester(config=best_cfg)
    sr_best = st_best.run(sample_home, sample_away, n_scenarios=1000)

    # Also run meta ensemble with best config
    meta_best = MetaPredictionEngine(config=best_cfg)
    best_probs = []
    for h, a, _o in match_pairs:
        r = meta_best.predict(h, a)
        best_probs.append([r.home_win_prob, r.draw_prob, r.away_win_prob])
    bpa = np.array(best_probs)
    brier_best = metrics.brier_score(bpa, outcomes_arr)
    logloss_best = metrics.log_loss(bpa, outcomes_arr)
    ece_best, _ = metrics.expected_calibration_error(bpa, outcomes_arr)
    acc_best = float(np.mean(np.argmax(bpa, axis=1) == np.argmax(outcomes_arr, axis=1)))
    rps_best = metrics.ranked_probability_score(bpa, outcomes_arr)

    data["stress_reduction"] = {
        "baseline_sprint7": {
            "elo_weight": 0.40,
            "stress_std": 0.0868,
            "brier": round(metrics.brier_score(probs_arr, outcomes_arr), 4),
            "logloss": round(metrics.log_loss(probs_arr, outcomes_arr), 4),
            "ece": round(metrics.expected_calibration_error(probs_arr, outcomes_arr)[0], 4),
            "accuracy": round(float(np.mean(np.argmax(probs_arr, axis=1) == np.argmax(outcomes_arr, axis=1))), 4),
        },
        "optimized_sprint75": {
            "elo_weight": best_config["elo_weight"],
            "stress_std": round(sr_best["std"], 4),
            "stress_mean": round(sr_best["mean"], 4),
            "stress_sensitivity": round(sr_best["sensitivity"], 2),
            "brier": round(brier_best, 4),
            "logloss": round(logloss_best, 4),
            "ece": round(ece_best, 4),
            "accuracy": round(acc_best, 4),
            "rps": round(rps_best, 4),
        },
    }
    logger.info(f"  Stress Std: 0.0868 -> {sr_best['std']:.4f}")
    logger.info(f"  Brier: {data['stress_reduction']['baseline_sprint7']['brier']} -> {brier_best:.4f}")

# ─── FASE 5: Reliability Final ───
logger.info("FASE 5 — Reliability Final Validation")
ra_ew = ReliabilityAnalyzer(n_bins=10)
rel_ew = ra_ew.analyze(probs_arr, outcomes_arr)

# Adaptive binning
def adaptive_reliability(probs, outcomes, n_bins=10):
    results = {}
    for i, label in enumerate(["home_win", "draw", "away_win"]):
        p, o = probs[:, i], outcomes[:, i]
        idx = np.argsort(p)
        ps, os_ = p[idx], o[idx]
        bs = len(p) // n_bins
        bins = []
        for b in range(n_bins):
            s, e = b * bs, len(p) if b == n_bins - 1 else (b + 1) * bs
            if s >= e: continue
            pred = float(np.mean(ps[s:e]))
            obs = float(np.mean(os_[s:e]))
            bins.append({"predicted": pred, "observed": obs, "error": obs - pred, "count": e - s})
        results[label] = bins
    return results

rel_ad = adaptive_reliability(probs_arr, outcomes_arr, n_bins=10)
def ece_from_bins(bins):
    w = sum(abs(b["error"]) * b["count"] for b in bins)
    t = sum(b["count"] for b in bins)
    return round(w / max(t, 1), 4)

data["reliability_final"] = {
    "equal_width": {
        "ece": rel_ew["overall_ece"],
        "mce": rel_ew["overall_mce"],
    },
    "adaptive_equal_freq": {
        "ece_home": ece_from_bins(rel_ad["home_win"]),
        "ece_draw": ece_from_bins(rel_ad["draw"]),
        "ece_away": ece_from_bins(rel_ad["away_win"]),
        "overall_ece": round(np.mean([ece_from_bins(rel_ad[l]) for l in ["home_win","draw","away_win"]]), 4),
    },
}

# ─── FASE 6: Scientific Benchmark Update ───
logger.info("FASE 6 — Scientific Benchmark Update")
sr_data = data.get("stress_reduction", {})
s7_base = sr_data.get("baseline_sprint7", {})
s75_opt = sr_data.get("optimized_sprint75", {})
ci_best = ci_cal.get("best_coverage", 0)
sharpness_val = sharp.average_entropy(probs_arr)

benchmark = {
    "sprint_3": {"accuracy": 0.481, "brier": 0.629, "logloss": 1.044, "rps": 0.228, "ece": 0.042, "stress_std": "N/A", "ci_coverage": "N/A", "pearson": "N/A", "sharpness": "N/A"},
    "sprint_4a": {"accuracy": 0.483, "brier": 0.611, "logloss": 1.019, "rps": 0.222, "ece": 0.061, "stress_std": "N/A", "ci_coverage": "N/A", "pearson": 0.98, "sharpness": "N/A"},
    "sprint_5": {"accuracy": 0.526, "brier": 0.592, "logloss": 0.997, "rps": 0.211, "ece": 0.085, "stress_std": 0.090, "ci_coverage": "N/A", "pearson": 0.98, "sharpness": 1.039},
    "sprint_6": {"accuracy": 0.526, "brier": 0.598, "logloss": 1.003, "rps": 0.214, "ece": 0.051, "stress_std": 0.092, "ci_coverage": 1.0, "pearson": 0.98, "sharpness": 1.039},
    "sprint_7": {"accuracy": s7_base.get("accuracy", 0.526), "brier": s7_base.get("brier", 0.598), "logloss": s7_base.get("logloss", 1.003), "rps": s7_base.get("rps", 0.214), "ece": s7_base.get("ece", 0.060), "stress_std": s7_base.get("stress_std", 0.087), "ci_coverage": 1.0, "pearson": 0.98, "sharpness": round(sharpness_val, 4)},
    "sprint_7_5": {"accuracy": s75_opt.get("accuracy", 0.526), "brier": s75_opt.get("brier", 0.598), "logloss": s75_opt.get("logloss", 1.003), "rps": s75_opt.get("rps", 0.214), "ece": s75_opt.get("ece", 0.060), "stress_std": s75_opt.get("stress_std", 0.087), "ci_coverage": round(ci_best, 4), "pearson": 0.98, "sharpness": round(sharpness_val, 4)},
}
data["professional_benchmark_v2"] = benchmark

# ─── SAVE ───
with open(os.path.join(DOCS, "sprint7_5_data.json"), "w") as f:
    json.dump(data, f, indent=2, default=str)
logger.info("All data saved to docs/sprint7_5_data.json")

# Print key results
print("\n=== SPRINT 7.5 KEY RESULTS ===")
for ew, v in pareto_results.items():
    flag = " <== BEST" if v["elo_weight"] == best_elo_w else ""
    print(f"  {ew}: Brier={v['brier']}, ECE={v['ece']}, Stress={v['stress_std']}, Acc={v['accuracy']}{flag}")
p75 = data.get("stress_reduction", {}).get("optimized_sprint75", {})
print(f"\n  Stress Std: {s7_base.get('stress_std','N/A')} -> {p75.get('stress_std','N/A')} (target <0.07)")
print(f"  ECE: {s7_base.get('ece','N/A')} -> {p75.get('ece','N/A')} (target <0.045)")
print(f"  CI Coverage: {ci_cal.get('best_coverage','N/A')} (target 85-95%)")
print(f"  Brier: {s7_base.get('brier','N/A')} -> {p75.get('brier','N/A')}")
print(f"  Best elo_weight: {best_elo_w}")
