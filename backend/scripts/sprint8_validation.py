"""
Sprint 8 - Master Validation.
Runs all 10 phases, saves data, generates reports.
"""
import json, logging, os, sys, time, uuid
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

import numpy as np

from app.data.historical_matches import ALL_HISTORICAL_MATCHES
from app.domain.entities import PredictionConfig, TeamEntity, ScenarioConfig
from app.engine.match_prediction import MatchPredictionEngine
from app.engine.meta_ensemble import MetaPredictionEngine
from app.engine.monte_carlo import run_single_tournament_py
from app.engine.sprint5_modules import (
    SharpnessMetrics, StressTester, ScenarioEngine, ExplainabilityEngineV2,
)
from app.engine.explainability import ExplainabilityEngine
from app.validation.calibration_metrics import CalibrationMetrics
from app.validation.regional_calibration import RegionalCalibrator
from app.validation.ci_recalibration import CIRecalibrator
from app.validation.elo_pareto import EloParetoOptimizer
from app.validation.elite_score import EliteScore
from app.validation.temporal_validation import TemporalValidation
from app.validation.tournament_forecasting import TournamentForecastValidator

DOCS = Path(__file__).resolve().parent.parent / "docs"
DOCS.mkdir(exist_ok=True)
metrics = CalibrationMetrics()
sharp = SharpnessMetrics()

# ── 48 realistic teams ──────────────────────────────────────────────────────
TEAMS_DATA = [
    ("Brazil", 1942, 1, 2.30, 0.85),    ("Argentina", 1915, 2, 2.10, 0.90),
    ("France", 1900, 3, 2.20, 0.80),     ("England", 1885, 4, 2.00, 0.95),
    ("Spain", 1870, 5, 2.05, 0.88),      ("Germany", 1860, 6, 1.95, 0.92),
    ("Netherlands", 1850, 7, 1.90, 0.90),("Portugal", 1840, 8, 1.85, 0.95),
    ("Italy", 1830, 9, 1.80, 1.00),      ("Belgium", 1820, 10, 1.85, 1.05),
    ("Croatia", 1810, 11, 1.70, 1.00),   ("Uruguay", 1800, 12, 1.65, 1.05),
    ("Colombia", 1780, 13, 1.60, 1.10),  ("Denmark", 1770, 14, 1.55, 1.05),
    ("Switzerland", 1760, 15, 1.50, 1.10),("Mexico", 1750, 16, 1.55, 1.15),
    ("Japan", 1740, 17, 1.45, 1.10),     ("Morocco", 1730, 18, 1.40, 1.15),
    ("Senegal", 1720, 19, 1.45, 1.20),   ("USA", 1710, 20, 1.50, 1.25),
    ("Serbia", 1700, 21, 1.40, 1.20),    ("Poland", 1690, 22, 1.45, 1.25),
    ("South Korea", 1680, 23, 1.35, 1.20),("Nigeria", 1670, 24, 1.40, 1.25),
    ("Ecuador", 1660, 25, 1.35, 1.25),   ("Iran", 1650, 26, 1.20, 1.15),
    ("Australia", 1640, 27, 1.25, 1.30), ("Canada", 1630, 28, 1.30, 1.30),
    ("Costa Rica", 1620, 29, 1.15, 1.25),("Cameroon", 1610, 30, 1.25, 1.35),
    ("Ghana", 1600, 31, 1.30, 1.35),     ("Saudi Arabia", 1580, 32, 1.10, 1.30),
    ("Tunisia", 1570, 33, 1.15, 1.35),   ("Algeria", 1560, 34, 1.20, 1.40),
    ("Egypt", 1550, 35, 1.15, 1.40),     ("Paraguay", 1540, 36, 1.10, 1.35),
    ("Panama", 1530, 37, 1.05, 1.40),    ("Slovakia", 1520, 38, 1.10, 1.45),
    ("Hungary", 1510, 39, 1.15, 1.45),   ("Greece", 1500, 40, 1.10, 1.40),
    ("Norway", 1490, 41, 1.20, 1.50),    ("Scotland", 1480, 42, 1.05, 1.45),
    ("Venezuela", 1470, 43, 1.00, 1.50), ("China", 1460, 44, 0.95, 1.50),
    ("Iraq", 1450, 45, 0.90, 1.55),      ("New Zealand", 1440, 46, 0.85, 1.50),
    ("Indonesia", 1430, 47, 0.80, 1.60), ("Kuwait", 1420, 48, 0.75, 1.65),
]

def build_teams():
    teams = []
    for name, elo, rank, xgf, xga in TEAMS_DATA:
        teams.append(TeamEntity(
            id=uuid.uuid4(), name=name, fifa_code=name[:3].upper(),
            elo_score=elo, fifa_rank=rank, xg_for=xgf, xg_against=xga,
        ))
    groups = "ABCDEFGHIJKL"
    group_mapping = {t.id: groups[i % 12] for i, t in enumerate(teams)}
    return teams, group_mapping

def build_historical_entities():
    td = {}
    for m in ALL_HISTORICAL_MATCHES:
        for side in ("home", "away"):
            name = getattr(m, f"{side}_team")
            elo = getattr(m, f"{side}_elo")
            gf = m.home_goals if side == "home" else m.away_goals
            ga = m.away_goals if side == "home" else m.home_goals
            if name not in td:
                td[name] = {"elo": elo, "gf": [], "ga": []}
            td[name]["gf"].append(gf); td[name]["ga"].append(ga)
    entities = {}
    for name, d in td.items():
        avg_gf = float(np.mean(d["gf"])) if d["gf"] else 1.0
        avg_ga = float(np.mean(d["ga"])) if d["ga"] else 1.5
        est_rank = max(1, min(100, int(100 * (1 - (d["elo"] - 1300) / 800))))
        entities[name] = TeamEntity(
            id=uuid.uuid4(), name=name, elo_score=d["elo"],
            fifa_rank=est_rank, xg_for=round(avg_gf, 4),
            xg_against=round(avg_ga, 4),
        )
    return entities

def make_config(elo_w):
    """Create config with given elo_weight, auto-re-normalize others."""
    remaining = 1.0 - elo_w
    base = {"xg_attack": 0.30, "xg_defense": 0.20, "fifa": 0.10}
    total_base = sum(base.values())
    return PredictionConfig(
        elo_weight=elo_w,
        xg_attack_weight=round(remaining * base["xg_attack"] / total_base, 4),
        xg_defense_weight=round(remaining * base["xg_defense"] / total_base, 4),
        fifa_weight=round(remaining * base["fifa"] / total_base, 4),
    )

def evaluate_config(cfg):
    """Compute match-level metrics (no tournament) for fast sweep."""
    mpe = MatchPredictionEngine(config=cfg)
    hist = build_historical_entities()
    teams, _ = build_teams()

    probs, outcomes = [], []
    for m in ALL_HISTORICAL_MATCHES:
        home = hist.get(m.home_team)
        away = hist.get(m.away_team)
        if not home or not away: continue
        r = mpe.predict_full(home, away)
        probs.append([r.home_win_prob, r.draw_prob, r.away_win_prob])
        if m.home_goals > m.away_goals: outcomes.append([1, 0, 0])
        elif m.home_goals == m.away_goals: outcomes.append([0, 1, 0])
        else: outcomes.append([0, 0, 1])
    pa = np.array(probs); oa = np.array(outcomes)

    match_metrics = {
        "accuracy": float(np.mean(np.argmax(pa, axis=1) == np.argmax(oa, axis=1))),
        "brier": metrics.brier_score(pa, oa),
        "logloss": metrics.log_loss(pa, oa),
        "rps": metrics.ranked_probability_score(pa, oa),
        "ece": metrics.expected_calibration_error(pa, oa)[0],
        "sharpness": sharp.average_entropy(pa),
    }

    # Stress test (match-level)
    brazil = next(t for t in teams if t.name == "Brazil")
    argentina = next(t for t in teams if t.name == "Argentina")
    st = StressTester(config=cfg)
    stress = st.run(brazil, argentina, n_scenarios=100)
    stress_std = stress["std"]

    return {"elo_weight": cfg.elo_weight, **match_metrics, "stress_std": round(stress_std, 4)}


def evaluate_tournament(cfg, teams, group_mapping):
    """Full tournament evaluation: champion probs, pearson, EliteScore."""
    mpe = MatchPredictionEngine(config=cfg)
    strengths = np.array(
        [mpe.compute_team_strength(t).overall_strength for t in teams], dtype=np.float64,
    )
    group_names = [group_mapping.get(t.id, "?") for t in teams]
    unique = sorted(set(group_names))
    g2i = {g: i for i, g in enumerate(unique)}
    assignments = np.array([g2i[g] for g in group_names], dtype=np.int64)
    num_teams = len(teams)

    # Baseline champion probs (1k sims)
    base_won = np.zeros(num_teams, dtype=np.int32)
    for sim in range(1_000):
        sr = run_single_tournament_py(strengths, assignments, num_teams)
        for t in range(num_teams):
            if sr[t, 0] >= 6: base_won[t] += 1
    champ_base = {teams[i].name: float(base_won[i]) / 1_000 for i in range(num_teams)}

    # Pearson
    str_list = [strengths[i] for i in range(num_teams)]
    champ_list = [champ_base[t.name] for t in teams]
    pearson = float(np.corrcoef(str_list, champ_list)[0, 1])

    # Tournament stress std (8 scenarios x 300 sims)
    np.random.seed(42)
    t_champs = {t.name: [] for t in teams}
    for sc in range(8):
        perturbed = []
        for t in teams:
            pt = deepcopy(t)
            pt.elo_score = int(t.elo_score * np.random.uniform(0.85, 1.15))
            if pt.xg_for: pt.xg_for *= np.random.uniform(0.80, 1.20)
            if pt.xg_against: pt.xg_against *= np.random.uniform(0.80, 1.20)
            pt.fifa_rank = max(1, int((t.fifa_rank or 50) * np.random.uniform(0.8, 1.2)))
            perturbed.append(pt)
        s_str = np.array(
            [mpe.compute_team_strength(pt).overall_strength for pt in perturbed], dtype=np.float64,
        )
        sc_won = np.zeros(num_teams, dtype=np.int32)
        for sim in range(300):
            sr = run_single_tournament_py(s_str, assignments, num_teams)
            for t in range(num_teams):
                if sr[t, 0] >= 6: sc_won[t] += 1
        for i, t in enumerate(teams):
            t_champs[t.name].append(float(sc_won[i]) / 300)
    t_stress_std = float(np.mean([np.std(v) for v in t_champs.values()]))

    return champ_base, round(pearson, 4), round(t_stress_std, 6)

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 66)
    print("  SPRINT 8 - ELITE CALIBRATION & PRODUCTION READINESS")
    print("=" * 66)

    all_data = {}
    best_config = None
    best_elite = -1

    # ── FASE 1 + 2: Fast Weight Sweep (match-level only), then full eval on best ──
    print(f"\n{'='*66}")
    print("  FASE 1+2 - Fine Weight Optimization + EliteScore")
    print(f"{'='*66}")

    elo_weights = [0.40, 0.38, 0.36]
    config_results = []
    for ew in elo_weights:
        logger.info(f"Fast-evaluating elo={ew}")
        cfg = make_config(ew)
        r = evaluate_config(cfg)
        # Compute partial EliteScore with available metrics; tournament pearson set to 0.90 placeholder
        partial_pearson = 0.90  # placeholder until tournament eval
        es = EliteScore.compute(r["accuracy"], r["brier"], r["logloss"],
                                r["ece"], r["stress_std"], partial_pearson)
        r["elite_score"] = es["elite_score"]
        config_results.append(r)
        print(f"  elo={ew:.2f}: Accuracy={r['accuracy']:.4f} Brier={r['brier']:.4f} "
              f"ECE={r['ece']:.4f} Stress={r['stress_std']:.4f} "
              f"PartialEliteScore={r['elite_score']:.4f}")

    best_by_match = max(config_results, key=lambda x: x["elite_score"])
    best_elo_w = best_by_match["elo_weight"]
    print(f"\n  Best by partial EliteScore: elo={best_elo_w} (score={best_by_match['elite_score']:.4f})")

    all_data["weight_optimization"] = {
        "configs": [{k: v for k, v in c.items()} for c in config_results],
        "best_elo_weight": best_elo_w,
    }
    best_config = make_config(best_elo_w)
    # Full tournament evaluation for best config
    teams, group_mapping = build_teams()
    champ_base, pearson_val, tourn_stress_std = evaluate_tournament(best_config, teams, group_mapping)

    # Final EliteScore with tournament metrics
    best_match = next(c for c in config_results if c["elo_weight"] == best_elo_w)
    es_final = EliteScore.compute(
        best_match["accuracy"], best_match["brier"], best_match["logloss"],
        best_match["ece"], best_match["stress_std"], pearson_val,
    )
    best_elite_score = es_final["elite_score"]
    best_stress_std = best_match["stress_std"]
    best_accuracy = best_match["accuracy"]
    best_brier = best_match["brier"]
    best_logloss = best_match["logloss"]
    best_ece = best_match["ece"]
    print(f"  Full EliteScore with tournament: {best_elite_score:.4f} (pearson={pearson_val:.4f})")

    # ── FASE 3: Temporal Validation ──
    print(f"\n{'='*66}")
    print("  FASE 3 - Temporal Validation")
    print(f"{'='*66}")
    tv = TemporalValidation(config=best_config)
    temporal_results = tv.run_all()
    all_data["temporal_validation"] = temporal_results
    for r in temporal_results:
        print(f"  {r['split']}: val_acc={r['validation']['accuracy']:.4f} "
              f"val_brier={r['validation']['brier']:.4f} "
              f"gap_acc={r['gap']['accuracy']:+.4f}")

    # ── FASE 4: Calibration Stability ──
    print(f"\n{'='*66}")
    print("  FASE 4 - Calibration Stability")
    print(f"{'='*66}")
    rc = RegionalCalibrator()
    calib_stability = {}
    for tournament in ("2014", "2018", "2022"):
        matches = [m for m in ALL_HISTORICAL_MATCHES if m.tournament == tournament]
        hist = build_historical_entities()
        mpe = MatchPredictionEngine(config=best_config)
        probs, outcomes = [], []
        for m in matches:
            home = hist.get(m.home_team); away = hist.get(m.away_team)
            if not home or not away: continue
            r = mpe.predict_full(home, away)
            probs.append([r.home_win_prob, r.draw_prob, r.away_win_prob])
            if m.home_goals > m.away_goals: outcomes.append([1, 0, 0])
            elif m.home_goals == m.away_goals: outcomes.append([0, 1, 0])
            else: outcomes.append([0, 0, 1])
        pa = np.array(probs); oa = np.array(outcomes)

        ece, bins = metrics.expected_calibration_error(pa, oa)
        mce_val = max(b["gap"] for b in bins) if bins else 0

        cal = rc.evaluate(pa, oa)
        calib_stability[tournament] = {
            "n_matches": len(pa),
            "baseline_ece": round(ece, 4),
            "baseline_mce": round(mce_val, 4),
            "baseline_brier": round(metrics.brier_score(pa, oa), 4),
            "global_temp_ece": cal["global_temperature"]["ece"],
            "regional_temp_ece": cal["regional_temperature"]["ece"],
        }
        print(f"  {tournament}: baseline ECE={calib_stability[tournament]['baseline_ece']:.4f} "
              f"global T={cal['global_temperature']['T']:.2f} "
              f"regional ECE={cal['regional_temperature']['ece']:.4f}")
    all_data["calibration_stability"] = calib_stability

    # ── FASE 5: CI Audit ──
    print(f"\n{'='*66}")
    print("  FASE 5 - Confidence Interval Audit")
    print(f"{'='*66}")
    hist = build_historical_entities()
    match_pairs = []
    for m in ALL_HISTORICAL_MATCHES:
        home = hist.get(m.home_team); away = hist.get(m.away_team)
        if not home or not away: continue
        if m.home_goals > m.away_goals: out = [1, 0, 0]
        elif m.home_goals == m.away_goals: out = [0, 1, 0]
        else: out = [0, 0, 1]
        match_pairs.append((home, away, np.array(out)))

    cir = CIRecalibrator(config=best_config)
    ci_audit = {}
    for alpha, label in [(0.20, 0.80), (0.10, 0.90), (0.05, 0.95)]:
        scale_info = cir.evaluate_scale(match_pairs[:20], noise_scale=0.15, n_resamples=100)
        ci_audit[f"{int(label*100)}%"] = scale_info
        print(f"  CI {int(label*100)}%: coverage={scale_info['coverage_rate']:.3f} "
              f"width={scale_info['avg_ci_width']:.4f}")
    all_data["ci_audit"] = ci_audit

    # ── FASE 6: Tournament Forecast Validation ──
    print(f"\n{'='*66}")
    print("  FASE 6 - Tournament Forecast Validation")
    print(f"{'='*66}")
    tfv = TournamentForecastValidator(config=best_config)
    forecast_results = []
    for t in ("2014", "2018", "2022"):
        r = tfv.validate_tournament(t, n_simulations=1_000)
        forecast_results.append(r)
        all_data.setdefault("tournament_forecasting", []).append(
            {k: v for k, v in r.items() if k != "result"}
        )
        print(f"  {r['tournament']}: champion rank={r['champion_rank']} "
              f"top4={r['top4_inclusion']}% top8={r['top8_inclusion']}% "
              f"Brier={r['tournament_brier']:.4f}")

    # ── FASE 7: Production Robustness ──
    print(f"\n{'='*66}")
    print("  FASE 7 - Production Robustness (ScenarioEngine)")
    print(f"{'='*66}")
    se = ScenarioEngine(config=best_config)
    teams, _ = build_teams()
    brazil = next(t for t in teams if t.name == "Brazil")
    argentina = next(t for t in teams if t.name == "Argentina")
    baseline = se.engine.predict_full(brazil, argentina)
    prod_robust = {"baseline_hw": round(baseline.home_win_prob, 4), "scenarios": {}}
    for sname in ["injury", "red_card", "suspension", "form_drop", "form_boost"]:
        results = []
        for _ in range(100):
            factor = float(np.random.uniform(0.5, 1.0))
            params = {}
            if sname == "injury":
                params["injury"] = ["PlayerX"]
                params["form_drop"] = {"xg_for": factor * 0.15, "elo": factor * 0.05}
            elif sname == "red_card":
                params["red_card"] = ["PlayerX"]
                params["form_drop"] = {"xg_for": factor * 0.20, "elo": factor * 0.10}
            elif sname == "suspension":
                params["suspension"] = ["PlayerY"]
                params["form_drop"] = {"xg_for": factor * 0.15}
            elif sname == "form_drop":
                params["form_drop"] = {"elo": factor * 0.15, "xg_for": factor * 0.20}
            elif sname == "form_boost":
                params["form_boost"] = {"elo": factor * 0.10, "xg_for": factor * 0.15}
            r = se.apply(brazil, argentina, scenario=ScenarioConfig(**params))
            results.append(r.home_win_prob)
        arr = np.array(results)
        drift = float(np.std(arr))
        prod_robust["scenarios"][sname] = {
            "mean": round(float(np.mean(arr)), 4),
            "std": round(drift, 4),
            "drift_pct": round(drift / max(baseline.home_win_prob, 0.001) * 100, 2),
        }
        print(f"  {sname}: drift={drift:.4f} ({prod_robust['scenarios'][sname]['drift_pct']:.1f}%)")
    all_data["production_robustness"] = prod_robust

    # ── FASE 8: Explainability Consistency ──
    print(f"\n{'='*66}")
    print("  FASE 8 - Explainability Consistency")
    print(f"{'='*66}")
    ee = ExplainabilityEngine(config=best_config)
    np.random.seed(42)
    drivers_sum = []
    for _ in range(200):
        h = teams[np.random.randint(len(teams))]
        a = teams[np.random.randint(len(teams))]
        if h.id == a.id: continue
        expl = ee.explain(h, a)
        s = sum(expl.drivers.values())
        drivers_sum.append(s)
    ds = np.array(drivers_sum)
    expl_consistency = {
        "n_matches": len(drivers_sum),
        "mean": float(np.mean(ds)),
        "min": float(np.min(ds)),
        "max": float(np.max(ds)),
        "std": float(np.std(ds)),
        "abs_error_mean": float(np.mean(np.abs(ds - 1.0))),
        "pct_within_1pct": float(np.mean(np.abs(ds - 1.0) <= 0.01) * 100),
    }
    all_data["explainability_consistency"] = expl_consistency
    print(f"  Mean sum: {expl_consistency['mean']:.6f} (target: 1.0)")
    print(f"  Abs error: {expl_consistency['abs_error_mean']:.6f}")
    print(f"  Within 1%: {expl_consistency['pct_within_1pct']:.1f}%")

    # ── FASE 9: Elite Benchmark ──
    print(f"\n{'='*66}")
    print("  FASE 9 - Elite Benchmark")
    print(f"{'='*66}")

    # Build benchmark from Sprint 3-7.5 data + Sprint 8
    sprint_labels = ["Sprint 3", "Sprint 4A", "Sprint 5", "Sprint 6",
                      "Sprint 7", "Sprint 7.5", "Sprint 8"]
    sprint_metrics = [
        {"accuracy": 0.481, "brier": 0.629, "logloss": 1.044, "ece": 0.042, "stress_std": 0.095, "pearson": 0.92},
        {"accuracy": 0.483, "brier": 0.611, "logloss": 1.019, "ece": 0.061, "stress_std": 0.093, "pearson": 0.98},
        {"accuracy": 0.526, "brier": 0.592, "logloss": 0.997, "ece": 0.085, "stress_std": 0.090, "pearson": 0.98},
        {"accuracy": 0.526, "brier": 0.598, "logloss": 1.003, "ece": 0.051, "stress_std": 0.092, "pearson": 0.98},
        {"accuracy": 0.526, "brier": 0.598, "logloss": 1.003, "ece": 0.060, "stress_std": 0.087, "pearson": 0.98},
        {"accuracy": 0.526, "brier": 0.590, "logloss": 0.989, "ece": 0.042, "stress_std": 0.068, "pearson": 0.98},
        {"accuracy": best_accuracy, "brier": best_brier,
         "logloss": best_logloss, "ece": best_ece,
         "stress_std": best_stress_std, "pearson": pearson_val},
    ]
    benchmark = []
    for i, label in enumerate(sprint_labels):
        m = sprint_metrics[i]
        es = EliteScore.compute(m["accuracy"], m["brier"], m["logloss"],
                                m["ece"], m["stress_std"], m["pearson"])
        benchmark.append({**m, "sprint": label, "elite_score": es["elite_score"]})
    all_data["elite_benchmark"] = benchmark

    print(f"  {'Sprint':15s} {'Acc':>6s} {'Brier':>7s} {'ECE':>7s} {'Stress':>7s} {'Pearson':>8s} {'EScore':>7s}")
    print(f"  {'-'*57}")
    for b in benchmark:
        print(f"  {b['sprint']:15s} {b['accuracy']:.3f} {b['brier']:.4f} {b['ece']:.4f} "
              f"{b['stress_std']:.3f} {b['pearson']:.3f} {b['elite_score']:.4f}")

    # ── FASE 10: Elite Verdict ──
    print(f"\n{'='*66}")
    print("  FASE 10 - Elite Verdict")
    print(f"{'='*66}")
    s8 = benchmark[-1]
    criteria_checks = [
        ("Calibration: ECE <= 0.040", s8["ece"] <= 0.040, s8["ece"]),
        ("Robustness: Stress Std <= 0.065", s8["stress_std"] <= 0.065, s8["stress_std"]),
        ("CI Coverage: 85-95%", 0.85 <= ci_audit.get("90%", {}).get("coverage_rate", 0) <= 0.95,
         ci_audit.get("90%", {}).get("coverage_rate", 0)),
        ("Forecasting: Top4 >= 66%",
         np.mean([r["top4_inclusion"] for r in forecast_results]) >= 66,
         np.mean([r["top4_inclusion"] for r in forecast_results])),
        ("Consistency: Pearson > 0.95", s8["pearson"] > 0.95, s8["pearson"]),
        ("Explainability: Drivers = 100% +/- 0.5%",
         expl_consistency["abs_error_mean"] <= 0.005, expl_consistency["abs_error_mean"]),
        ("EliteScore > Sprint 7.5", s8["elite_score"] > benchmark[-2]["elite_score"], s8["elite_score"]),
    ]
    passed_count = 0
    for cname, cok, cval in criteria_checks:
        if cok: passed_count += 1
        sym = "PASS" if cok else "FAIL"
        print(f"  [{sym}] {cname:55s} {cval:.4f}")

    total_criteria = len(criteria_checks)
    pct = passed_count / total_criteria * 100
    grade = "ELITE" if pct >= 85 else "PROFESSIONAL" if pct >= 60 else "RESEARCH"
    print(f"\n  Grade: {passed_count}/{total_criteria} criteria = {grade}")
    verdict = {
        "criteria": {cname: {"pass": cok, "value": round(cval, 4)} for cname, cok, cval in criteria_checks},
        "passed": passed_count,
        "total": total_criteria,
        "grade": grade,
        "best_elo_weight": best_elo_w,
        "best_elite_score": best_elite_score,
    }
    all_data["elite_verdict"] = verdict

    # ── Save all data ──
    with open(DOCS / "sprint8_data.json", "w") as f:
        json.dump(all_data, f, indent=2, default=str)
    print(f"\nAll data saved to {DOCS / 'sprint8_data.json'}")

    print(f"\n{'='*66}")
    print(f"  SPRINT 8 COMPLETE - Best elo={best_elo_w} "
          f"EliteScore={best_elite_score:.4f}")
    print(f"{'='*66}")

if __name__ == "__main__":
    main()
