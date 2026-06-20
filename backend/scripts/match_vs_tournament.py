"""
Sprint 4A — FASE 6: Match vs Tournament Consistency.

Calculates Pearson and Spearman correlation between:
- match_strength (from attack/defense composite used in predict_full)
- overall_strength (from weighted all-signal composite used in Monte Carlo)

For each team, computes both strengths and correlates them across all teams.
Target: r > 0.80.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from scipy.stats import pearsonr, spearmanr
from app.data.historical_matches import ALL_HISTORICAL_MATCHES
from app.domain.entities import PredictionConfig
from app.engine.match_prediction import MatchPredictionEngine
from app.validation.backtesting import BacktestingEngine

DOCS = os.path.join(os.path.dirname(__file__), "..", "docs")
os.makedirs(DOCS, exist_ok=True)

config = PredictionConfig()
engine = MatchPredictionEngine(config=config)
bt = BacktestingEngine(config=config)

# Build teams from all tournaments
team_data = bt._extract_team_data(ALL_HISTORICAL_MATCHES)

team_strengths = []
for name, data in team_data.items():
    team = bt._build_team_entity(name, data)
    ts = engine.compute_team_strength(team)
    team_strengths.append({
        "team": name,
        "attack_strength": round(ts.attack_strength, 4),
        "defense_strength": round(ts.defense_strength, 4),
        "overall_strength": round(ts.overall_strength, 4),
        "match_strength": round((ts.attack_strength + ts.defense_strength) / 2, 4),
        "elo": team.elo_score,
        "xg_for": team.xg_for,
        "xg_against": team.xg_against,
        "fifa_rank": team.fifa_rank,
    })

# Extract arrays
match_s = np.array([t["match_strength"] for t in team_strengths])
overall_s = np.array([t["overall_strength"] for t in team_strengths])
attack_s = np.array([t["attack_strength"] for t in team_strengths])
defense_s = np.array([t["defense_strength"] for t in team_strengths])

# Correlations
pearson_r, pearson_p = pearsonr(match_s, overall_s)
spearman_r, spearman_p = spearmanr(match_s, overall_s)

print(f"Teams analyzed: {len(team_strengths)}")
print(f"\nMatch Strength vs Overall Strength:")
print(f"  Pearson r:  {pearson_r:.6f}  (p={pearson_p:.2e})")
print(f"  Spearman r: {spearman_r:.6f}  (p={spearman_p:.2e})")
print(f"  Target: r > 0.80 -> {'PASS' if pearson_r > 0.80 else 'FAIL'}")

# Additional: attack <-> overall, defense <-> overall
pa, _ = pearsonr(attack_s, overall_s)
pd, _ = pearsonr(defense_s, overall_s)
print(f"\n  Attack vs Overall:   r={pa:.6f}")
print(f"  Defense vs Overall:  r={pd:.6f}")

# Top/bottom 5 teams
print(f"\nTop 5 by overall_strength:")
for t in sorted(team_strengths, key=lambda x: x["overall_strength"], reverse=True)[:5]:
    print(f"  {t['team']:20s} overall={t['overall_strength']:.4f} match={t['match_strength']:.4f} atk={t['attack_strength']:.4f} def={t['defense_strength']:.4f}")

print(f"\nBottom 5 by overall_strength:")
for t in sorted(team_strengths, key=lambda x: x["overall_strength"])[:5]:
    print(f"  {t['team']:20s} overall={t['overall_strength']:.4f} match={t['match_strength']:.4f} atk={t['attack_strength']:.4f} def={t['defense_strength']:.4f}")

# Save
result = {
    "n_teams": len(team_strengths),
    "pearson_match_vs_overall": round(pearson_r, 6),
    "pearson_p": round(float(pearson_p), 6),
    "spearman_match_vs_overall": round(spearman_r, 6),
    "spearman_p": round(float(spearman_p), 6),
    "pearson_attack_vs_overall": round(pa, 6),
    "pearson_defense_vs_overall": round(pd, 6),
    "pass_criteria": bool(pearson_r > 0.80),
    "teams": team_strengths,
}

with open(os.path.join(DOCS, "match_vs_tournament_data.json"), "w") as f:
    json.dump(result, f, indent=2)
print(f"\nSaved to docs/match_vs_tournament_data.json")
