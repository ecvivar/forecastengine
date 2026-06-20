"""
Sprint 2C — FASE 5: Ranking Validation.

Compare Top 10 Elo, Top 10 xG, Top 10 FIFA ranks against
Top 10 Monte Carlo champion probabilities.

Measure Spearman and Pearson correlations.

Output:
  - docs/ranking_validation.md
  - docs/ranking_data.json
"""

import json
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["LOG_LEVEL"] = "WARNING"

import numpy as np
from scipy.stats import pearsonr, spearmanr

from app.domain.entities import SimulationConfig, TeamEntity
from app.engine.monte_carlo import MonteCarloEngine


def make_team(name, elo, fifa_rank, xg_for, xg_against):
    return TeamEntity(
        id=uuid.uuid4(),
        name=name,
        elo_score=elo,
        fifa_rank=fifa_rank,
        xg_for=xg_for,
        xg_against=xg_against,
    )


def build_realistic_teams():
    """Same 48 teams as the stability test."""
    teams_data = [
        ("Brazil", 1942, 1, 2.30, 0.85),
        ("Argentina", 1915, 2, 2.10, 0.90),
        ("France", 1900, 3, 2.20, 0.80),
        ("England", 1885, 4, 2.00, 0.95),
        ("Spain", 1870, 5, 2.05, 0.88),
        ("Germany", 1860, 6, 1.95, 0.92),
        ("Netherlands", 1850, 7, 1.90, 0.90),
        ("Portugal", 1840, 8, 1.85, 0.95),
        ("Italy", 1830, 9, 1.80, 1.00),
        ("Belgium", 1820, 10, 1.85, 1.05),
        ("Croatia", 1810, 11, 1.70, 1.00),
        ("Uruguay", 1800, 12, 1.65, 1.05),
        ("Colombia", 1780, 13, 1.60, 1.10),
        ("Denmark", 1770, 14, 1.55, 1.05),
        ("Switzerland", 1760, 15, 1.50, 1.10),
        ("Mexico", 1750, 16, 1.55, 1.15),
        ("Japan", 1740, 17, 1.45, 1.10),
        ("Morocco", 1730, 18, 1.40, 1.15),
        ("Senegal", 1720, 19, 1.45, 1.20),
        ("USA", 1710, 20, 1.50, 1.25),
        ("Serbia", 1700, 21, 1.40, 1.20),
        ("Poland", 1690, 22, 1.45, 1.25),
        ("South Korea", 1680, 23, 1.35, 1.20),
        ("Nigeria", 1670, 24, 1.40, 1.25),
        ("Ecuador", 1660, 25, 1.35, 1.25),
        ("Iran", 1650, 26, 1.20, 1.15),
        ("Australia", 1640, 27, 1.25, 1.30),
        ("Canada", 1630, 28, 1.30, 1.30),
        ("Costa Rica", 1620, 29, 1.15, 1.25),
        ("Cameroon", 1610, 30, 1.25, 1.35),
        ("Ghana", 1600, 31, 1.30, 1.35),
        ("Saudi Arabia", 1580, 32, 1.10, 1.30),
        ("Tunisia", 1570, 33, 1.15, 1.35),
        ("Algeria", 1560, 34, 1.20, 1.40),
        ("Egypt", 1550, 35, 1.15, 1.40),
        ("Paraguay", 1540, 36, 1.10, 1.35),
        ("Panama", 1530, 37, 1.05, 1.40),
        ("Slovakia", 1520, 38, 1.10, 1.45),
        ("Hungary", 1510, 39, 1.15, 1.45),
        ("Greece", 1500, 40, 1.10, 1.40),
        ("Norway", 1490, 41, 1.20, 1.50),
        ("Scotland", 1480, 42, 1.05, 1.45),
        ("Venezuela", 1470, 43, 1.00, 1.50),
        ("China", 1460, 44, 0.95, 1.50),
        ("Iraq", 1450, 45, 0.90, 1.55),
        ("New Zealand", 1440, 46, 0.85, 1.50),
        ("Indonesia", 1430, 47, 0.80, 1.60),
        ("Kuwait", 1420, 48, 0.75, 1.65),
    ]
    teams = []
    for name, elo, rank, xgf, xga in teams_data:
        teams.append(make_team(name, elo, rank, xgf, xga))
    groups = "ABCDEFGHIJKL"
    group_mapping = {}
    for i, t in enumerate(teams):
        group_mapping[t.id] = groups[i % 12]
    return teams, group_mapping


teams, group_mapping = build_realistic_teams()
team_names = [t.name for t in teams]

# Run MC at 50000
print("Running Monte Carlo (50000 simulations)...")
config = SimulationConfig(num_simulations=50000, parallel=False)
engine = MonteCarloEngine(config=config)
results = engine.run(teams, group_mapping)

# Build per-team data
team_data = {}
for t in teams:
    team_data[t.name] = {
        "elo": t.elo_score,
        "fifa_rank": t.fifa_rank,
        "xg_for": t.xg_for,
        "xg_against": t.xg_against,
    }

prob_data = {}
for r in results:
    prob_data[r.team_name] = {
        "champion_pct": round(r.won_count / 50000 * 100, 2),
        "finalist_pct": round(r.final_count / 50000 * 100, 2),
        "semi_pct": round(r.semi_final_count / 50000 * 100, 2),
    }

print(f"\n{'='*70}")
print("FASE 5 — RANKING VALIDATION")
print(f"{'='*70}")

# ── Top 10 by each metric ──
print(f"\n{'Team':<18} {'Elo':>6} {'xG_for':>8} {'FIFA':>6} {'Champ%':>8} {'Final%':>8} {'Semi%':>8}")
print(f"{'-'*62}")

# All teams sorted by champion probability
all_by_champion = sorted(team_names, key=lambda n: prob_data[n]["champion_pct"], reverse=True)
for name in all_by_champion:
    d = team_data[name]
    p = prob_data[name]
    print(f"{name:<18} {d['elo']:>6} {d['xg_for']:>8.2f} {d['fifa_rank']:>6} {p['champion_pct']:>7.2f}% {p['finalist_pct']:>7.2f}% {p['semi_pct']:>7.2f}%")

# ── Correlations ──
print(f"\n{'='*70}")
print("CORRELATIONS WITH CHAMPION PROBABILITY")
print(f"{'='*70}")

from app.engine.match_prediction import MatchPredictionEngine
mpe = MatchPredictionEngine()
overall_strengths = [mpe.compute_team_strength(t).overall_strength for t in teams]

features = {
    "Elo Score": [team_data[n]["elo"] for n in team_names],
    "xG For": [team_data[n]["xg_for"] for n in team_names],
    "xG Against": [team_data[n]["xg_against"] for n in team_names],
    "FIFA Rank": [team_data[n]["fifa_rank"] for n in team_names],
    "Overall Strength": overall_strengths,
}

champ_probs = [prob_data[n]["champion_pct"] for n in team_names]

print(f"\n{'Feature':<30} {'Pearson r':>10} {'p-value':>10} {'Spearman rho':>12} {'p-value':>10}")
print(f"{'-'*72}")

correlations = {}
for feat_name, feat_vals in features.items():
    x = np.array(feat_vals)
    y = np.array(champ_probs)

    if np.std(x) == 0 or np.std(y) == 0:
        print(f"{feat_name:<30} {'N/A':>10} {'N/A':>10} {'N/A':>12} {'N/A':>10}")
        continue

    # Pearson
    pearson_r, pearson_p = pearsonr(x, y)
    # Spearman
    spearman_rho, spearman_p = spearmanr(x, y)

    correlations[feat_name] = {
        "pearson_r": round(pearson_r, 4),
        "pearson_p": round(pearson_p, 6),
        "spearman_rho": round(spearman_rho, 4),
        "spearman_p": round(spearman_p, 6),
    }

    print(f"{feat_name:<30} {pearson_r:>10.4f} {pearson_p:>10.6f} {spearman_rho:>12.4f} {spearman_p:>10.6f}")

# ── Top 10 Elo vs Top 10 Champion Prob ──
print(f"\n{'='*70}")
print("TOP 10 BY ELO vs TOP 10 BY CHAMPION PROBABILITY")
print(f"{'='*70}")

top10_elo = sorted(team_names, key=lambda n: team_data[n]["elo"], reverse=True)[:10]
top10_champ = sorted(team_names, key=lambda n: prob_data[n]["champion_pct"], reverse=True)[:10]

print(f"\n{'Rank':<6} {'Top 10 Elo':<18} {'Elo':>6} {'Champ%':>8}   {'Top 10 Champ Prob':<18} {'Elo':>6} {'Champ%':>8}")
print(f"{'-'*72}")
for i in range(10):
    e_name = top10_elo[i]
    c_name = top10_champ[i]
    print(f"{i+1:<6} {e_name:<18} {team_data[e_name]['elo']:>6} {prob_data[e_name]['champion_pct']:>7.2f}%   {c_name:<18} {team_data[c_name]['elo']:>6} {prob_data[c_name]['champion_pct']:>7.2f}%")

# Overlap
elo_but_not_champ = set(top10_elo) - set(top10_champ)
champ_but_not_elo = set(top10_champ) - set(top10_elo)
overlap = set(top10_elo) & set(top10_champ)
print(f"\nOverlap in Top 10: {len(overlap)}/10")
if elo_but_not_champ:
    print(f"  Top 10 Elo but NOT Top 10 Champ: {', '.join(sorted(elo_but_not_champ))}")
if champ_but_not_elo:
    print(f"  Top 10 Champ but NOT Top 10 Elo: {', '.join(sorted(champ_but_not_elo))}")

# ── Top 10 xG_for vs Top 10 Champ Prob ──
print(f"\n{'='*70}")
print("TOP 10 BY xG FOR vs TOP 10 BY CHAMPION PROBABILITY")
print(f"{'='*70}")

top10_xg = sorted(team_names, key=lambda n: team_data[n]["xg_for"], reverse=True)[:10]

print(f"\n{'Rank':<6} {'Top 10 xG For':<18} {'xG_f':>6} {'Champ%':>8}   {'Top 10 Champ Prob':<18} {'xG_f':>6} {'Champ%':>8}")
print(f"{'-'*72}")
for i in range(10):
    x_name = top10_xg[i]
    c_name = top10_champ[i]
    print(f"{i+1:<6} {x_name:<18} {team_data[x_name]['xg_for']:>6.2f} {prob_data[x_name]['champion_pct']:>7.2f}%   {c_name:<18} {team_data[c_name]['xg_for']:>6.2f} {prob_data[c_name]['champion_pct']:>7.2f}%")

xg_but_not_champ = set(top10_xg) - set(top10_champ)
champ_but_not_xg = set(top10_champ) - set(top10_xg)
xg_overlap = set(top10_xg) & set(top10_champ)
print(f"\nOverlap in Top 10: {len(xg_overlap)}/10")
if xg_but_not_champ:
    print(f"  Top 10 xG but NOT Top 10 Champ: {', '.join(sorted(xg_but_not_champ))}")
if champ_but_not_xg:
    print(f"  Top 10 Champ but NOT Top 10 xG: {', '.join(sorted(champ_but_not_xg))}")


# ── Save data ──
os.makedirs("docs", exist_ok=True)
output = {
    "correlations": correlations,
    "team_data": team_data,
    "prob_data": prob_data,
    "rankings": {
        "top10_elo": top10_elo,
        "top10_xg": top10_xg,
        "top10_champ": top10_champ,
        "overlap_elo_champ": len(overlap),
        "overlap_xg_champ": len(xg_overlap),
    }
}
with open("docs/ranking_data.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, default=str)

print(f"\nData saved to docs/ranking_data.json")
print("Done.")