"""
Sprint 4A — FASE 3: WeightOptimizer v2.

After the Sprint 4A engine changes, all four weights (elo, xg_attack,
xg_defense, fifa) now affect predict_full(). This optimizer grids over
valid weight combos and measures ACTUAL metric differences.

Runs full grid search and reports Top 20 configurations.
"""
import json, os, sys, logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from app.domain.entities import PredictionConfig
from app.validation.weight_optimizer import WeightOptimizer

DOCS = os.path.join(os.path.dirname(__file__), "..", "docs")
os.makedirs(DOCS, exist_ok=True)
logging.basicConfig(level=logging.INFO)

optimizer = WeightOptimizer()
result = optimizer.search()

# Report top 20
print(f"Total candidates evaluated: {result['n_candidates']}")
print(f"\nTop 20 configurations (by log_loss, then brier):")
print(f"{'Rank':<6} {'elo':<8} {'xg_atk':<8} {'xg_def':<8} {'fifa':<8} {'Brier':<12} {'LogLoss':<12}")
print("-" * 66)
for i, r in enumerate(result["results"][:20]):
    w = r["weights"]
    print(f"{i+1:<6} {w['elo']:<8} {w['xg_attack']:<8} {w['xg_defense']:<8} {w['fifa']:<8} {r['brier']:<12} {r['log_loss']:<12}")

# Compare current vs best
best = result["best_weights"]
curr = result["current_weights"]
print(f"\nCurrent weights: {curr}")
print(f"Best found:      {best}")
print(f"Current metrics: Brier={result['current_metrics']['brier']:.6f}, LogLoss={result['current_metrics']['log_loss']:.6f}")
print(f"Best metrics:    Brier={result['best_metrics']['brier']:.6f}, LogLoss={result['best_metrics']['log_loss']:.6f}")
print(f"Improvement:     Brier delta={result['improvement']['brier_delta']:.6f}, LogLoss delta={result['improvement']['log_loss_delta']:.6f}")

# Save for report
with open(os.path.join(DOCS, "weight_optimizer_v2_data.json"), "w") as f:
    json.dump({
        "current_weights": result["current_weights"],
        "current_metrics": result["current_metrics"],
        "best_weights": result["best_weights"],
        "best_metrics": result["best_metrics"],
        "improvement": result["improvement"],
        "n_candidates": result["n_candidates"],
        "top20": result["results"][:20],
    }, f, indent=2)

print(f"\nSaved to docs/weight_optimizer_v2_data.json")
