"""
Sprint 4A — FASE 7: Final Benchmark.

Compares the Sprint 3 model (before weights affected predict_full)
against the Sprint 4A model (after FIFA integration + weight-aware engine).

Metrics: Accuracy, Brier, LogLoss, RPS, ECE on 192 historical matches.

Runs both configs:
  - Sprint 3 "old" engine: uses old _compute_team_strength (attack=xG, defense=xG)
  - Sprint 4A "new" engine: uses weighted composites + Elo-weighted Bayesian prior
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from app.data.historical_matches import ALL_HISTORICAL_MATCHES
from app.domain.entities import PredictionConfig, TeamEntity, TeamStrength
from app.engine.match_prediction import MatchPredictionEngine
from app.validation.calibration_metrics import CalibrationMetrics
from app.validation.backtesting import BacktestingEngine

DOCS = os.path.join(os.path.dirname(__file__), "..", "docs")
os.makedirs(DOCS, exist_ok=True)


def run_benchmark(with_engine_changes=True):
    """
    Run benchmark on 192 matches.
    
    If with_engine_changes=False:
      Simulates OLD behavior by using a patched engine that mimics old
      _compute_team_strength (attack_strength=attack_xg, defense_strength=defense_xg)
      and old _bayesian_update (fixed prior strength).
    """
    config = PredictionConfig()
    engine = MatchPredictionEngine(config=config)
    metrics = CalibrationMetrics()
    bt = BacktestingEngine(config=config)

    # Monkey-patch for OLD behavior
    if not with_engine_changes:
        old_strength = engine._compute_team_strength
        def old_compute(team):
            ts = old_strength(team)
            # Override to xG-only attack/defense
            if team.xg_for is not None and team.xg_for > 0:
                atk = team.xg_for / 1.5
                atk = max(0.3, min(3.0, atk))
            else:
                atk = 1.0
            if team.xg_against is not None and team.xg_against > 0:
                deff = 1.5 / team.xg_against
                deff = max(0.3, min(3.0, deff))
            else:
                deff = 1.0
            return TeamStrength(attack_strength=atk, defense_strength=deff, overall_strength=ts.overall_strength)
        engine._compute_team_strength = old_compute

        old_bayes = engine._bayesian_update
        def old_bayes_update(hw, dr, aw, eh, ea):
            """Original Bayesian prior: fixed ps=0.5, no elo_weight scaling."""
            elo_diff = eh - ea
            elo_expected_home = 1.0 / (1.0 + 10.0 ** (-elo_diff / 400.0))
            prior_home = elo_expected_home
            prior_draw = 0.25
            prior_away = 1.0 - prior_home - prior_draw
            if prior_away < 0.0:
                prior_away = 0.0
                total_prior = prior_home + prior_draw + prior_away
                prior_home /= total_prior
                prior_draw /= total_prior
            ps = 0.5
            total = ps + 1.0
            uh = (ps * prior_home + hw) / total
            ud = (ps * prior_draw + dr) / total
            ua = (ps * prior_away + aw) / total
            total_p = uh + ud + ua
            return {"home_win": uh / total_p, "draw": ud / total_p, "away_win": ua / total_p}
        engine._bayesian_update = old_bayes_update

    team_data = bt._extract_team_data(ALL_HISTORICAL_MATCHES)
    team_entities = {name: bt._build_team_entity(name, d) for name, d in team_data.items()}

    probs, outcomes = [], []
    correct = 0
    total = 0
    for m in ALL_HISTORICAL_MATCHES:
        home = team_entities.get(m.home_team)
        away = team_entities.get(m.away_team)
        if not home or not away:
            continue
        r = engine.predict_full(home, away, home_advantage=True)
        probs.append([r.home_win_prob, r.draw_prob, r.away_win_prob])

        if m.home_goals > m.away_goals:
            actual = [1, 0, 0]
            pred_class = 0
        elif m.home_goals == m.away_goals:
            actual = [0, 1, 0]
            pred_class = 1
        else:
            actual = [0, 0, 1]
            pred_class = 2

        outcomes.append(actual)
        if np.argmax([r.home_win_prob, r.draw_prob, r.away_win_prob]) == pred_class:
            correct += 1
        total += 1

    probs_arr = np.array(probs)
    outcomes_arr = np.array(outcomes)
    accuracy = correct / total if total > 0 else 0

    return {
        "accuracy": round(accuracy, 6),
        "brier": round(metrics.brier_score(probs_arr, outcomes_arr), 6),
        "log_loss": round(metrics.log_loss(probs_arr, outcomes_arr), 6),
        "rps": round(metrics.ranked_probability_score(probs_arr, outcomes_arr), 6),
        "ece": round(metrics.expected_calibration_error(probs_arr, outcomes_arr)[0], 6),
        "matches": total,
    }


print("Running Sprint 3 (old) benchmark...")
old = run_benchmark(with_engine_changes=False)

print("Running Sprint 4A (new) benchmark...")
new = run_benchmark(with_engine_changes=True)

# Comparison table
print(f"\n{'Metric':<12} {'Sprint 3':<14} {'Sprint 4A':<14} {'Delta':<14}")
print("-" * 54)
for metric in ["accuracy", "brier", "log_loss", "rps", "ece"]:
    ov = old[metric]
    nv = new[metric]
    delta = nv - ov
    print(f"{metric:<12} {ov:<14} {nv:<14} {delta:+.6f}")

# Determine success criteria
success = {
    "accuracy_improved_or_maintained": new["accuracy"] >= old["accuracy"],
    "brier_improved": new["brier"] <= old["brier"],
    "ece_improved": new["ece"] <= old["ece"],
    "all_pass": all([
        new["accuracy"] >= old["accuracy"],
        new["brier"] <= old["brier"],
        new["ece"] <= old["ece"],
    ]),
}
print(f"\nSuccess Criteria:")
for k, v in success.items():
    print(f"  {k}: {'PASS' if v else 'FAIL'}")

# Save
comparison = {
    "Sprint3": old,
    "Sprint4A": new,
    "success_criteria": {k: bool(v) for k, v in success.items()},
    "deltas": {
        "accuracy": round(new["accuracy"] - old["accuracy"], 6),
        "brier": round(new["brier"] - old["brier"], 6),
        "log_loss": round(new["log_loss"] - old["log_loss"], 6),
        "rps": round(new["rps"] - old["rps"], 6),
        "ece": round(new["ece"] - old["ece"], 6),
    },
}

with open(os.path.join(DOCS, "sprint4a_benchmark_data.json"), "w") as f:
    json.dump(comparison, f, indent=2)
print(f"\nSaved to docs/sprint4a_benchmark_data.json")
