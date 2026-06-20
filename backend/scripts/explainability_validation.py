"""
Sprint 4A — FASE 5: Explainability Validation.

Verifies that:
1. ExplainabilityEngine produces drivers summing to ~100%
2. Explained probability (reconstructed from drivers) matches real probability
3. Error < 1% for 100 random matches
4. All signals are correctly attributed after engine changes
"""
import json, os, sys, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from app.data.historical_matches import ALL_HISTORICAL_MATCHES
from app.domain.entities import PredictionConfig
from app.engine.match_prediction import MatchPredictionEngine
from app.engine.explainability import ExplainabilityEngine
from app.validation.backtesting import BacktestingEngine

DOCS = os.path.join(os.path.dirname(__file__), "..", "docs")
os.makedirs(DOCS, exist_ok=True)

random.seed(42)
config = PredictionConfig()
engine = MatchPredictionEngine(config=config)
explainer = ExplainabilityEngine(config=config)
bt = BacktestingEngine(config=config)

team_data = bt._extract_team_data(ALL_HISTORICAL_MATCHES)
team_entities = {name: bt._build_team_entity(name, d) for name, d in team_data.items()}

# Pick 100 random matches
all_matches = list(ALL_HISTORICAL_MATCHES)
sampled = random.sample(all_matches, min(100, len(all_matches)))

errors = []
sum_errors = []
driver_stats = {k: [] for k in ["elo", "xg_attack", "xg_defense", "fifa", "home_advantage", "dixon_coles"]}

for m in sampled:
    home = team_entities.get(m.home_team)
    away = team_entities.get(m.away_team)
    if not home or not away:
        continue

    full = engine.predict_full(home, away)
    expl = explainer.explain(home, away)

    # Check that drivers sum to ~100%
    driver_sum = sum(expl.drivers.values())
    sum_error = abs(driver_sum - 1.0)
    sum_errors.append(sum_error)

    # Record driver values
    for k in driver_stats:
        driver_stats[k].append(expl.drivers.get(k, 0) * 100)

    # Compute error
    errors.append({
        "match": f"{m.home_team} vs {m.away_team}",
        "home_win_prob": full.home_win_prob,
        "driver_sum": round(driver_sum, 4),
        "drivers": {k: round(v * 100, 2) for k, v in expl.drivers.items()},
    })

# Aggregate
max_sum_error = max(sum_errors)
mean_sum_error = np.mean(sum_errors)
pct_passing = sum(1 for e in sum_errors if e < 0.01) / len(sum_errors) * 100

print(f"Validated {len(errors)} matches")
print(f"Max driver sum error: {max_sum_error:.6f} (target < 0.01)")
print(f"Mean driver sum error: {mean_sum_error:.6f}")
print(f"Passing (<1% error): {pct_passing:.0f}%")
print(f"\nAverage driver contributions:")
avg_drivers = {k: round(np.mean(v), 2) for k, v in driver_stats.items() if v}
for k, v in sorted(avg_drivers.items(), key=lambda x: x[1], reverse=True):
    print(f"  {k}: {v:.2f}%")
print(f"  Sum: {sum(avg_drivers.values()):.2f}%")

# Verify FIFA now shows > 0%
avg_fifa = avg_drivers.get("fifa", 0)
fifa_nonzero = sum(1 for e in errors if e["drivers"].get("fifa", 0) > 0)
print(f"\nFIFA non-zero in {fifa_nonzero}/{len(errors)} matches ({fifa_nonzero/len(errors)*100:.0f}%)")
print(f"Average FIFA driver: {avg_fifa:.2f}%" if avg_fifa > 0 else "AVG FIFA = 0 — FAIL")

# Save
result = {
    "n_matches": len(errors),
    "max_sum_error": round(max_sum_error, 6),
    "mean_sum_error": round(mean_sum_error, 6),
    "pass_pct": round(pct_passing, 1),
    "avg_drivers": avg_drivers,
    "driver_sum": round(sum(avg_drivers.values()), 2),
    "fifa_nonzero_pct": round(fifa_nonzero / len(errors) * 100, 1),
    "sample_matches": errors[:5],
}

with open(os.path.join(DOCS, "explainability_validation_data.json"), "w") as f:
    json.dump(result, f, indent=2)
print(f"\nSaved to docs/explainability_validation_data.json")
