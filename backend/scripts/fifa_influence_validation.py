"""
Sprint 4A — FASE 2: FIFA Influence Validation.

Verifies that FIFA rank produces 1-10% influence on match-level predictions
after the _compute_team_strength changes (attack/defense weighted composites).
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from app.domain.entities import PredictionConfig, TeamEntity
from app.engine.match_prediction import MatchPredictionEngine
from app.engine.explainability import ExplainabilityEngine

DOCS = os.path.join(os.path.dirname(__file__), "..", "docs")
os.makedirs(DOCS, exist_ok=True)

def make_team(name, elo=1500, xg_for=1.5, xg_against=1.5, fifa_rank=100):
    import uuid
    return TeamEntity(
        id=uuid.uuid4(), name=name, elo_score=elo,
        fifa_rank=fifa_rank, xg_for=xg_for, xg_against=xg_against,
    )

# Scenarios — varying FIFA rank gap
scenarios = [
    ("Equal FIFA (both rank 50)", 1500, 1.5, 1.5, 50, 1500, 1.5, 1.5, 50),
    ("Big FIFA gap (10 vs 150)", 1600, 1.8, 1.2, 10, 1400, 1.2, 1.8, 150),
    ("Same Elo/xG, FIFA gap only (5 vs 100)", 1500, 1.5, 1.5, 5, 1500, 1.5, 1.5, 100),
    ("Strong team good FIFA vs weak team bad FIFA", 1800, 2.0, 1.0, 5, 1300, 1.0, 2.0, 150),
    ("FIFA offsetting weak xG", 1500, 1.0, 2.0, 2, 1500, 2.0, 1.0, 200),
]

engine = MatchPredictionEngine()
explainer = ExplainabilityEngine()

results = []
for label, he, hxgf, hxga, hf, ae, axgf, axga, af in scenarios:
    home = make_team("Home", he, hxgf, hxga, hf)
    away = make_team("Away", ae, axgf, axga, af)
    r = engine.predict_full(home, away)
    expl = explainer.explain(home, away)
    fifa_pct = expl.drivers.get("fifa", 0) * 100

    # Also compare: prediction with real FIFA vs FIFA-neutralized
    home_neutral = make_team("Home", he, hxgf, hxga, 100)
    away_neutral = make_team("Away", ae, axgf, axga, 100)
    r_neutral = engine.predict_full(home_neutral, away_neutral)

    hw_delta = abs(r.home_win_prob - r_neutral.home_win_prob) * 100

    entry = {
        "scenario": label,
        "home_win_prob": round(r.home_win_prob, 4),
        "draw_prob": round(r.draw_prob, 4),
        "away_win_prob": round(r.away_win_prob, 4),
        "fifa_driver_pct": round(fifa_pct, 2),
        "fifa_driver_delta_pp": round(hw_delta, 4),
        "home_fifa_rank": hf,
        "away_fifa_rank": af,
        "home_elo": he,
        "away_elo": ae,
        "home_xg_for": hxgf,
        "away_xg_for": axgf,
    }
    results.append(entry)
    print(f"{label}: home_win={entry['home_win_prob']:.4f}, fifa={fifa_pct:.2f}%, delta={hw_delta:.4f}pp")

# Overall FIFA influence across 192 historical matches
print("\n--- FIFA influence across 192 historical matches ---")
from app.data.historical_matches import ALL_HISTORICAL_MATCHES
from app.validation.backtesting import BacktestingEngine

bt = BacktestingEngine()
team_data = bt._extract_team_data(ALL_HISTORICAL_MATCHES)
team_entities = {name: bt._build_team_entity(name, d) for name, d in team_data.items()}

fifa_influences = []
for m in ALL_HISTORICAL_MATCHES:
    home_ent = team_entities.get(m.home_team)
    away_ent = team_entities.get(m.away_team)
    if not home_ent or not away_ent:
        continue
    expl = explainer.explain(home_ent, away_ent)
    fifa_influences.append(expl.drivers.get("fifa", 0) * 100)

fifa_arr = np.array(fifa_influences)
summary = {
    "min_pct": round(float(fifa_arr.min()), 2),
    "max_pct": round(float(fifa_arr.max()), 2),
    "mean_pct": round(float(fifa_arr.mean()), 2),
    "median_pct": round(float(np.median(fifa_arr)), 2),
    "p25_pct": round(float(np.percentile(fifa_arr, 25)), 2),
    "p75_pct": round(float(np.percentile(fifa_arr, 75)), 2),
    "count": int(len(fifa_arr)),
}
print(f"FIFA influence over {summary['count']} matches:")
for k, v in summary.items():
    print(f"  {k}: {v}" if k != "count" else f"  {k}: {v}")

results.append(summary)

# Save to JSON for report generation
with open(os.path.join(DOCS, "fifa_validation_data.json"), "w") as f:
    json.dump(results, f, indent=2)

print(f"\nData saved to docs/fifa_validation_data.json")
