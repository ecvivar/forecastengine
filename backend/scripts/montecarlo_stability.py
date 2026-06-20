"""
Sprint 2C — FASE 3 & 4: Monte Carlo Stability + Probability Consistency Audit.

FASE 3: Run MC at 100/500/1000/5000/10000/50000 simulations, track convergence.
FASE 4: Verify probability sums (champion=100%, finalist=200%, etc.) at each N.

Output:
  - docs/montecarlo_stability.md
  - docs/probability_audit.md
  - docs/montecarlo_data.json
"""

import json
import os
import sys
import uuid
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["LOG_LEVEL"] = "WARNING"

import numpy as np

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
    """
    Build 48 synthetic teams with realistic World Cup 2026 profiles.
    Powers range from elite (Elo ~1950) to weak (Elo ~1350).
    """
    teams_data = [
        # (name, elo, fifa_rank, xg_for, xg_against)
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
    for i, (name, elo, rank, xgf, xga) in enumerate(teams_data):
        t = make_team(name, elo, rank, xgf, xga)
        teams.append(t)

    # Assign groups A-L (12 groups of 4)
    groups = "ABCDEFGHIJKL"
    group_mapping = {}
    for i, t in enumerate(teams):
        group_mapping[t.id] = groups[i % 12]

    return teams, group_mapping


# Build teams once
teams, group_mapping = build_realistic_teams()
print(f"Built {len(teams)} teams in {len(set(group_mapping.values()))} groups")


def run_mc(n_sims: int, parallel: bool = False) -> list:
    """Run Monte Carlo with given number of simulations."""
    config = SimulationConfig(num_simulations=n_sims, parallel=parallel)
    engine = MonteCarloEngine(config=config)
    start = time.time()
    results = engine.run(teams, group_mapping)
    elapsed = time.time() - start
    return results, elapsed


def compute_probabilities(results, n_sims):
    """Convert TournamentResult counts to probabilities."""
    probs = {}
    for r in results:
        probs[r.team_name] = {
            "team_name": r.team_name,
            "group_name": r.group_name,
            "champion_pct": round(r.won_count / n_sims * 100, 2),
            "finalist_pct": round(r.final_count / n_sims * 100, 2),
            "semi_pct": round(r.semi_final_count / n_sims * 100, 2),
            "quarter_pct": round(r.quarter_final_count / n_sims * 100, 2),
            "round16_pct": round(r.round_of_16_count / n_sims * 100, 2),
            "round32_pct": round(r.round_of_32_count / n_sims * 100, 2),
        }
    return probs


def audit_probability_sums(probs_by_sim, n_sims):
    """Verify that probability sums satisfy expected totals."""
    expected = {
        "champion_pct": 100.0,
        "finalist_pct": 200.0,
        "semi_pct": 400.0,
        "quarter_pct": 800.0,
        "round16_pct": 1600.0,
        "round32_pct": 3200.0,
    }
    audit = {"n_simulations": n_sims, "checks": {}}
    for stage, expected_pct in expected.items():
        total = sum(p[stage] for p in probs_by_sim.values())
        deviation = round(total - expected_pct, 4)
        audit["checks"][stage] = {
            "expected": expected_pct,
            "actual": round(total, 4),
            "deviation": deviation,
            "pass": abs(deviation) < 0.5,  # allow 0.5pp rounding error
        }
    all_pass = all(v["pass"] for v in audit["checks"].values())
    audit["all_pass"] = all_pass
    return audit


# ── Run simulations at different sizes ──
sim_sizes = [100, 500, 1000, 5000, 10000, 50000]
# Reduce for speed: use smaller max or adjust based on time constraints
# Actually, let's include all but note the 50k may take a while
print(f"\nSimulation sizes: {sim_sizes}")

all_results = {}
all_probs = {}
timings = {}
audits = {}

for n in sim_sizes:
    print(f"\n{'='*60}")
    print(f"Running {n} simulations...")
    sys.stdout.flush()
    results, elapsed = run_mc(n, parallel=False)
    probs = compute_probabilities(results, n)
    all_results[n] = results
    all_probs[n] = probs
    timings[n] = round(elapsed, 2)

    audit = audit_probability_sums(probs, n)
    audits[n] = audit

    top10 = sorted(probs.values(), key=lambda x: x["champion_pct"], reverse=True)[:10]
    print(f"  Time: {elapsed:.2f}s")
    print(f"  Top 10 champions:")
    for i, t in enumerate(top10, 1):
        print(f"    {i:2d}. {t['team_name']:<16} {t['champion_pct']:>6.2f}%")
    print(f"  Probability audit: {'PASS' if audit['all_pass'] else 'FAIL'}")
    for stage, v in audit["checks"].items():
        status = "OK" if v["pass"] else "DEV"
        print(f"    {stage:<16}: {v['actual']:>8.2f}% (expected {v['expected']:>5.1f}%) [{status}]")
    sys.stdout.flush()


# ── FASE 3: Convergence Analysis ──
print("\n" + "=" * 60)
print("FASE 3 — CONVERGENCE ANALYSIS")
print("=" * 60)

prev_probs = None
prev_n = None
convergence = {}

for n in sim_sizes:
    probs = all_probs[n]
    top10 = sorted(probs.values(), key=lambda x: x["champion_pct"], reverse=True)[:10]
    top10_names = [t["team_name"] for t in top10]

    deltas = {}
    if prev_probs is not None:
        for t in top10_names:
            if t in prev_probs:
                delta = abs(probs[t]["champion_pct"] - prev_probs[t]["champion_pct"])
                deltas[t] = round(delta, 3)
        max_delta = max(deltas.values()) if deltas else 0
        mean_delta = round(np.mean(list(deltas.values())), 3) if deltas else 0
    else:
        max_delta = 0
        mean_delta = 0

    convergence[n] = {
        "top10": top10,
        "max_delta_from_prev": max_delta,
        "mean_delta_from_prev": mean_delta,
        "prev_n": prev_n,
        "elapsed_s": timings[n],
    }

    print(f"\n--- n={n:>6d} (elapsed: {timings[n]:>6.2f}s) ---")
    if prev_n:
        print(f"  vs n={prev_n}: max delta={max_delta:.3f}pp, mean delta={mean_delta:.3f}pp")
    for i, t in enumerate(top10, 1):
        lbl = f"{i:2d}. {t['team_name']:<16}"
        ci = f"{t['champion_pct']:>6.2f}%"
        if prev_n and t["team_name"] in prev_probs:
            d = t["champion_pct"] - prev_probs[t["team_name"]]["champion_pct"]
            ci += f" ({'+' if d > 0 else ''}{d:+.3f})"
        print(f"    {lbl} {ci}")

    prev_probs = probs
    prev_n = n


# ── FASE 4: Probability Audit Summary ──
print("\n" + "=" * 60)
print("FASE 4 — PROBABILITY CONSISTENCY AUDIT SUMMARY")
print("=" * 60)

print(f"\n{'N sims':>8} {'Status':>8}", end="")
for stage in ["champion_pct", "finalist_pct", "semi_pct", "quarter_pct", "round16_pct", "round32_pct"]:
    print(f" {stage:>12}", end="")
print()

for n in sim_sizes:
    a = audits[n]
    status = "PASS" if a["all_pass"] else "FAIL"
    print(f"{n:>8} {status:>8}", end="")
    for stage in ["champion_pct", "finalist_pct", "semi_pct", "quarter_pct", "round16_pct", "round32_pct"]:
        print(f" {a['checks'][stage]['actual']:>12.4f}", end="")
    print()


# ── Save all data ──
os.makedirs("docs", exist_ok=True)
output = {
    "sim_sizes": sim_sizes,
    "timings": timings,
    "convergence": {
        str(n): {
            "top10": [
                {"team": t["team_name"], "champion_pct": t["champion_pct"],
                 "finalist_pct": t["finalist_pct"], "semi_pct": t["semi_pct"]}
                for t in conv["top10"]
            ],
            "max_delta_from_prev": conv["max_delta_from_prev"],
            "mean_delta_from_prev": conv["mean_delta_from_prev"],
            "prev_n": conv["prev_n"],
            "elapsed_s": conv["elapsed_s"],
        }
        for n, conv in convergence.items()
    },
    "audits": {
        str(n): a for n, a in audits.items()
    },
}
with open("docs/montecarlo_data.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, default=str)

print("\nData saved to docs/montecarlo_data.json")
print("Done.")
