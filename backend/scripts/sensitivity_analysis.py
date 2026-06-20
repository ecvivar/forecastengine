"""
Sprint 2C — FASE 1 & 2: Sensitivity Analysis + Ablation Testing.

Measures individual impact of Elo, xG attack, xG defense, FIFA, HA, Bayesian prior,
and Dixon-Coles on match probabilities and expected goals.

Also performs ablation testing (FASE 2) by removing one signal at a time.

Output:
  - Console tables
  - docs/sensitivity_report.md
  - docs/feature_importance_report.md
"""

import json
import os
import sys
import uuid
from copy import deepcopy

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["LOG_LEVEL"] = "WARNING"

import numpy as np

from app.domain.entities import PredictionConfig, TeamEntity
from app.engine.match_prediction import MatchPredictionEngine


def make_team(
    name: str,
    elo: int = 1800,
    fifa_rank: int = 10,
    xg_for: float = 1.8,
    xg_against: float = 1.2,
) -> TeamEntity:
    """Create a synthetic TeamEntity with given parameters."""
    return TeamEntity(
        id=uuid.uuid4(),
        name=name,
        elo_score=elo,
        fifa_rank=fifa_rank,
        xg_for=xg_for,
        xg_against=xg_against,
    )


# ── Baseline teams ──────────────────────────────────────────────
# Team A = strong, Team B = average (World Cup typical)
TEAM_A = make_team("Baseline_Strong", elo=1850, fifa_rank=5, xg_for=2.0, xg_against=1.0)
TEAM_B = make_team("Baseline_Average", elo=1600, fifa_rank=30, xg_for=1.3, xg_against=1.5)

engine = MatchPredictionEngine()


def predict(home: TeamEntity, away: TeamEntity) -> dict:
    """Run full prediction and return key metrics."""
    r = engine.predict_full(home, away, home_advantage=True)
    return {
        "home_win_pct": round(r.home_win_prob * 100, 2),
        "draw_pct": round(r.draw_prob * 100, 2),
        "away_win_pct": round(r.away_win_prob * 100, 2),
        "home_xg": r.home_expected_goals,
        "away_xg": r.away_expected_goals,
    }


def fmt_row(label: str, data: dict, baseline: dict | None = None) -> str:
    """Format a table row with optional delta from baseline."""
    parts = [f"| {label:<25}"]
    for k in ["home_win_pct", "draw_pct", "away_win_pct", "home_xg", "away_xg"]:
        v = data[k]
        if baseline is not None:
            delta = v - baseline[k]
            sign = "+" if delta > 0 else ""
            parts.append(f" {v:>6.2f} ({sign}{delta:>5.2f})")
        else:
            parts.append(f" {v:>13.2f}")
    parts.append(" |")
    return "".join(parts)


# ═══════════════════════════════════════════════════════════════
# SENSITIVITY: Baseline
# ═══════════════════════════════════════════════════════════════
print("=" * 80)
print("SPRINT 2C — SENSITIVITY ANALYSIS")
print("=" * 80)

baseline_home = predict(TEAM_A, TEAM_B)
print("\n--- BASELINE (Strong vs Average) ---")
print(f"  Team A: Elo={TEAM_A.elo_score}, FIFA={TEAM_A.fifa_rank}, xG_for={TEAM_A.xg_for}, xG_against={TEAM_A.xg_against}")
print(f"  Team B: Elo={TEAM_B.elo_score}, FIFA={TEAM_B.fifa_rank}, xG_for={TEAM_B.xg_for}, xG_against={TEAM_B.xg_against}")
print(f"  Result: {baseline_home}")

# ═══════════════════════════════════════════════════════════════
# 1. ELO SENSITIVITY
# ═══════════════════════════════════════════════════════════════
print("\n" + "-" * 70)
print("1. ELO SENSITIVITY (vary Team A elo, keep everything else fixed)")
print("-" * 70)

elo_cases = [0, 50, 100, 200, 300]
elo_results = {}
for delta in elo_cases:
    team = deepcopy(TEAM_A)
    team.elo_score = 1850 + delta
    r = predict(team, TEAM_B)
    elo_results[f"+{delta}"] = r

header = "| Parameter                  | home_win_pct     | draw_pct        | away_win_pct    | home_xg          | away_xg          |"
sep = "|" + "-" * 26 + "|" + "-" * 18 + "|" + "-" * 18 + "|" + "-" * 18 + "|" + "-" * 18 + "|" + "-" * 18 + "|"
print(header)
print(sep)
for delta in elo_cases:
    lbl = f"Elo +{delta}" if delta > 0 else "Elo baseline"
    print(fmt_row(lbl, elo_results[f"+{delta}"], elo_results["+0"]))

# ═══════════════════════════════════════════════════════════════
# 2. xG ATTACK SENSITIVITY
# ═══════════════════════════════════════════════════════════════
print("\n" + "-" * 70)
print("2. xG ATTACK SENSITIVITY (vary Team A xG_for)")
print("-" * 70)

xg_atk_cases = [0, 0.10, 0.20, 0.30, 0.50]
xg_atk_results = {}
for pct in xg_atk_cases:
    team = deepcopy(TEAM_A)
    team.xg_for = 2.0 * (1.0 + pct)
    r = predict(team, TEAM_B)
    xg_atk_results[f"+{int(pct*100)}%"] = r

print(header)
print(sep)
for pct in xg_atk_cases:
    lbl = f"xG_atk +{int(pct*100)}%" if pct > 0 else "xG_atk baseline"
    print(fmt_row(lbl, xg_atk_results[f"+{int(pct*100)}%"], xg_atk_results["+0%"]))


# ═══════════════════════════════════════════════════════════════
# 3. xG DEFENSE SENSITIVITY
# ═══════════════════════════════════════════════════════════════
print("\n" + "-" * 70)
print("3. xG DEFENSE SENSITIVITY (vary Team A xG_against — lower is better)")
print("-" * 70)

xg_def_cases = [(0, "0%"), (-0.10, "-10%"), (-0.20, "-20%"), (-0.30, "-30%")]
xg_def_results = {}
for delta, label in xg_def_cases:
    team = deepcopy(TEAM_A)
    team.xg_against = 1.0 * (1.0 + delta)
    r = predict(team, TEAM_B)
    xg_def_results[label] = r

print(header)
print(sep)
for delta, label in xg_def_cases:
    lbl = f"xG_def {label}" if delta < 0 else "xG_def baseline"
    print(fmt_row(lbl, xg_def_results[label], xg_def_results["0%"]))


# ═══════════════════════════════════════════════════════════════
# 4. FIFA RANK SENSITIVITY
# ═══════════════════════════════════════════════════════════════
print("\n" + "-" * 70)
print("4. FIFA RANK SENSITIVITY (vary Team A rank)")
print("-" * 70)

fifa_cases = [5, 15, 30, 60]
fifa_results = {}
for rank in fifa_cases:
    team = deepcopy(TEAM_A)
    team.fifa_rank = rank
    r = predict(team, TEAM_B)
    fifa_results[rank] = r

print(header)
print(sep)
for rank in fifa_cases:
    lbl = f"FIFA rank {rank}"
    print(fmt_row(lbl, fifa_results[rank], fifa_results[5]))


# ═══════════════════════════════════════════════════════════════
# 5. HOME ADVANTAGE / PRIOR / DIXON-COLES SENSITIVITY
# ═══════════════════════════════════════════════════════════════
print("\n" + "-" * 70)
print("5. PARAMETER SENSITIVITY (HA, Bayesian Prior, Dixon-Coles)")

cfg_results = {}
base_result = predict(TEAM_A, TEAM_B)

# Home Advantage off
cfg = deepcopy(engine.config)
cfg.home_advantage = 0.0
engine_no_ha = MatchPredictionEngine(config=cfg)
r = engine_no_ha.predict_full(TEAM_A, TEAM_B, home_advantage=True)
cfg_results["HA=0.0"] = {"home_win_pct": round(r.home_win_prob * 100, 2),
                          "draw_pct": round(r.draw_prob * 100, 2),
                          "away_win_pct": round(r.away_win_prob * 100, 2),
                          "home_xg": r.home_expected_goals,
                          "away_xg": r.away_expected_goals}

# HA * 2
cfg2 = deepcopy(engine.config)
cfg2.home_advantage = 0.16
engine_ha2 = MatchPredictionEngine(config=cfg2)
r = engine_ha2.predict_full(TEAM_A, TEAM_B, home_advantage=True)
cfg_results["HA=0.16"] = {"home_win_pct": round(r.home_win_prob * 100, 2),
                           "draw_pct": round(r.draw_prob * 100, 2),
                           "away_win_pct": round(r.away_win_prob * 100, 2),
                           "home_xg": r.home_expected_goals,
                           "away_xg": r.away_expected_goals}

# Bayesian prior = 0 (no prior)
cfg3 = deepcopy(engine.config)
cfg3.bayesian_prior_strength = 0.0
engine_no_prior = MatchPredictionEngine(config=cfg3)
r = engine_no_prior.predict_full(TEAM_A, TEAM_B, home_advantage=True)
cfg_results["Prior=0.0"] = {"home_win_pct": round(r.home_win_prob * 100, 2),
                             "draw_pct": round(r.draw_prob * 100, 2),
                             "away_win_pct": round(r.away_win_prob * 100, 2),
                             "home_xg": r.home_expected_goals,
                             "away_xg": r.away_expected_goals}

# Bayesian prior = 2.0 (original)
cfg4 = deepcopy(engine.config)
cfg4.bayesian_prior_strength = 2.0
engine_prior2 = MatchPredictionEngine(config=cfg4)
r = engine_prior2.predict_full(TEAM_A, TEAM_B, home_advantage=True)
cfg_results["Prior=2.0"] = {"home_win_pct": round(r.home_win_prob * 100, 2),
                             "draw_pct": round(r.draw_prob * 100, 2),
                             "away_win_pct": round(r.away_win_prob * 100, 2),
                             "home_xg": r.home_expected_goals,
                             "away_xg": r.away_expected_goals}

# Dixon-Coles off
cfg5 = deepcopy(engine.config)
cfg5.dixon_coles_tau = 0.0
engine_no_dc = MatchPredictionEngine(config=cfg5)
r = engine_no_dc.predict_full(TEAM_A, TEAM_B, home_advantage=True)
cfg_results["DC=0.0"] = {"home_win_pct": round(r.home_win_prob * 100, 2),
                          "draw_pct": round(r.draw_prob * 100, 2),
                          "away_win_pct": round(r.away_win_prob * 100, 2),
                          "home_xg": r.home_expected_goals,
                          "away_xg": r.away_expected_goals}

# Neutral venue
r = engine.predict_full(TEAM_A, TEAM_B, home_advantage=False)
cfg_results["Neutral"] = {"home_win_pct": round(r.home_win_prob * 100, 2),
                          "draw_pct": round(r.draw_prob * 100, 2),
                          "away_win_pct": round(r.away_win_prob * 100, 2),
                          "home_xg": r.home_expected_goals,
                          "away_xg": r.away_expected_goals}

print(header)
print(sep)
for lbl, r in cfg_results.items():
    print(fmt_row(lbl, r, base_result))


# ═══════════════════════════════════════════════════════════════
# FASE 2: ABLATION TESTING
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("FASE 2 — ABLATION TESTING")
print("=" * 80)
print("\nRemoving one signal at a time and measuring impact on 5 team pairs.\n")

# Define 5 diverse team pairs
PAIRS = [
    ("Elite vs Weak", make_team("Elite", elo=1950, fifa_rank=1, xg_for=2.5, xg_against=0.8),
                       make_team("Weak", elo=1400, fifa_rank=60, xg_for=0.8, xg_against=2.2)),
    ("Strong vs Avg", TEAM_A, TEAM_B),
    ("Avg vs Avg", make_team("AvgA", elo=1650, fifa_rank=25, xg_for=1.4, xg_against=1.4),
                   make_team("AvgB", elo=1600, fifa_rank=35, xg_for=1.3, xg_against=1.5)),
    ("Def vs Def", make_team("DefA", elo=1700, fifa_rank=15, xg_for=1.0, xg_against=0.9),
                   make_team("DefB", elo=1650, fifa_rank=20, xg_for=0.9, xg_against=1.0)),
    ("Atk vs Atk", make_team("AtkA", elo=1750, fifa_rank=10, xg_for=2.2, xg_against=1.8),
                   make_team("AtkB", elo=1700, fifa_rank=12, xg_for=2.0, xg_against=1.6)),
]


def run_pred(home, away, config_override=None, team_mod=None):
    """Run prediction with optional config override and team data modification."""
    e = MatchPredictionEngine(config=config_override or PredictionConfig())
    h = deepcopy(home)
    a = deepcopy(away)
    if team_mod:
        team_mod(h, a)
    return e.predict_full(h, a, home_advantage=True)


def extract(r):
    return {
        "home_win_pct": round(r.home_win_prob * 100, 2),
        "draw_pct": round(r.draw_prob * 100, 2),
        "away_win_pct": round(r.away_win_prob * 100, 2),
        "home_xg": r.home_expected_goals,
        "away_xg": r.away_expected_goals,
    }


# Ablation definitions: (name, config_override, team_mod)
# We must directly modify team data or critical config params, because
# elo_weight / xg_attack_weight only affect overall_strength (used by Monte Carlo),
# NOT attack_strength / defense_strength (used by match prediction).
def no_mod(h, a): pass

def strip_xg(h, a):
    h.xg_for = a.xg_for = None
    h.xg_against = a.xg_against = None

def strip_elo_prior(h, a):
    pass  # config handles this

def strip_dc(h, a):
    pass  # config handles this

def equalize_elo(h, a):
    avg = (h.elo_score + a.elo_score) // 2
    h.elo_score = a.elo_score = avg

def swap_xg(h, a):
    h.xg_for, a.xg_for = a.xg_for, h.xg_for
    h.xg_against, a.xg_against = a.xg_against, h.xg_against

ablations = [
    ("full", PredictionConfig(), no_mod),
    ("no_xg", PredictionConfig(), strip_xg),
    ("no_elo_prior", PredictionConfig(bayesian_prior_strength=0.0), no_mod),
    ("no_dc", PredictionConfig(dixon_coles_tau=0.0), no_mod),
    ("equal_elo", PredictionConfig(), equalize_elo),
    ("swap_xg", PredictionConfig(), swap_xg),
]

# Ablation results: [pair_name][abl_name] = metrics
ablation_data = {}
for pair_name, home, away in PAIRS:
    ablation_data[pair_name] = {}
    for abl_name, cfg, mod in ablations:
        r = run_pred(home, away, config_override=cfg, team_mod=mod)
        ablation_data[pair_name][abl_name] = extract(r)

# Print ablation tables
for pair_name, home, away in PAIRS:
    print(f"\n--- {pair_name}: {home.name} vs {away.name} ---")
    print(f"    Elo: {home.elo_score} vs {away.elo_score}")
    print(f"    xG_for: {home.xg_for} vs {away.xg_for}")
    print(f"    xG_against: {home.xg_against} vs {away.xg_against}")
    print(f"    FIFA: {home.fifa_rank} vs {away.fifa_rank}")
    print(header)
    print(sep)
    full = ablation_data[pair_name]["full"]
    for abl_name, _, _ in ablations:
        r = ablation_data[pair_name][abl_name]
        print(fmt_row(f"  {abl_name}", r, full))

# Compute aggregate impact
print("\n\n--- AGGREGATE ABLATION IMPACT (avg abs delta across 5 pairs) ---")
signals = ["no_xg", "no_elo_prior", "no_dc", "equal_elo", "swap_xg"]
metrics_to_measure = ["home_win_pct", "home_xg"]

agg_impact = {}
for sig in signals:
    agg_impact[sig] = {}
    for metric in metrics_to_measure:
        deltas = []
        for pair_name, _, _ in PAIRS:
            full_val = ablation_data[pair_name]["full"][metric]
            ablated_val = ablation_data[pair_name][sig][metric]
            deltas.append(abs(full_val - ablated_val))
        agg_impact[sig][metric] = {
            "mean_delta": round(np.mean(deltas), 3),
            "max_delta": round(max(deltas), 3),
            "std_delta": round(np.std(deltas), 3),
        }

print(f"\n{'Signal':<12} {'Metric':<15} {'Mean D':>8} {'Max D':>8} {'Std D':>8}")
print("-" * 55)
for sig in signals:
    for metric in metrics_to_measure:
        d = agg_impact[sig][metric]
        print(f"{sig:<12} {metric:<15} {d['mean_delta']:>8.3f} {d['max_delta']:>8.3f} {d['std_delta']:>8.3f}")


# Normalize importance to percentages
print("\n\n--- RELATIVE FEATURE IMPORTANCE (normalized by total mean delta) ---")
# For the match prediction engine, signals that affect the output are:
# xG data (attack+defense), Elo prior, Dixon-Coles
# Note: FIFA does NOT affect predict_full directly (only Monte Carlo).
print("\n  Note: FIFA weight only affects overall_strength (Monte Carlo), not predict_full.")
print("  The ablation below measures what happens when we remove each signal at the data level.\n")
total_mean_hw = sum(agg_impact[sig]["home_win_pct"]["mean_delta"] for sig in signals)
total_mean_xg = sum(agg_impact[sig]["home_xg"]["mean_delta"] for sig in signals)

# Use UTF-8 output to a file for proper characters, then print simplified
print(f"\n{'Signal':<16} {'HomeWin Delta':>14} {'xG Delta':>14}")
print("-" * 46)
for sig in signals:
    hw = agg_impact[sig]["home_win_pct"]["mean_delta"]
    xg = agg_impact[sig]["home_xg"]["mean_delta"]
    print(f"{sig:<16} {hw:>13.3f} {xg:>13.3f}")

# ── Save JSON data for reports ──
os.makedirs("docs", exist_ok=True)
output = {
    "baseline": {
        "team_a": {"elo": TEAM_A.elo_score, "fifa": TEAM_A.fifa_rank, "xg_for": TEAM_A.xg_for, "xg_against": TEAM_A.xg_against},
        "team_b": {"elo": TEAM_B.elo_score, "fifa": TEAM_B.fifa_rank, "xg_for": TEAM_B.xg_for, "xg_against": TEAM_B.xg_against},
        "result": baseline_home,
    },
    "elo_sensitivity": elo_results,
    "xg_attack_sensitivity": xg_atk_results,
    "xg_defense_sensitivity": xg_def_results,
    "fifa_sensitivity": fifa_results,
    "parameter_sensitivity": cfg_results,
    "ablation": {
        pair_name: ablation_data[pair_name] for pair_name, _, _ in PAIRS
    },
    "aggregate_impact": agg_impact,
}
with open("docs/sensitivity_data.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, default=str)

print("\n\nData saved to docs/sensitivity_data.json")
print("Done. Run with: python backend/scripts/sensitivity_analysis.py")
