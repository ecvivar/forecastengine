"""Run backtesting + weight optimization for Sprint 3 FASE 2 & 3."""
import json, os, sys
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['LOG_LEVEL'] = 'WARNING'
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.validation.backtesting import BacktestingEngine
from app.validation.weight_optimizer import WeightOptimizer

print("=" * 60)
print("FASE 2 — Historical Backtesting")
print("=" * 60)

be = BacktestingEngine()
results = be.run_all(n_simulations=500)
for r in results:
    print(f"\n{r.tournament}:")
    print(f"  Predicted champion: {r.predicted_champion} ({r.champion_probability}%)")
    print(f"  Actual champion:    {r.real_champion}")
    print(f"  Top4 accuracy:      {r.top4_accuracy}")
    print(f"  Finalist accuracy:  {r.finalist_accuracy}")
    print(f"  Avg Brier:          {r.avg_brier}")
    print(f"  Avg Log Loss:       {r.avg_log_loss}")
    print(f"  Avg RPS:            {r.avg_rps}")
    print(f"  ECE:                {r.ece}")
    print(f"  Matches:            {r.match_count}")

os.makedirs("docs", exist_ok=True)
with open("docs/backtest_results.json", "w", encoding="utf-8") as f:
    json.dump([{
        "tournament": r.tournament,
        "predicted_champion": r.predicted_champion,
        "real_champion": r.real_champion,
        "champion_probability": r.champion_probability,
        "top4_accuracy": r.top4_accuracy,
        "finalist_accuracy": r.finalist_accuracy,
        "avg_brier": r.avg_brier,
        "avg_log_loss": r.avg_log_loss,
        "avg_rps": r.avg_rps,
        "ece": r.ece,
        "match_count": r.match_count,
        "n_simulations": r.n_simulations,
    } for r in results], f, indent=2, default=str)

print("\n" + "=" * 60)
print("FASE 3 — Weight Optimization")
print("=" * 60)

wo = WeightOptimizer()
opt = wo.search()

if opt.get("best_weights"):
    print(f"\nBest weights found:")
    for k, v in opt["best_weights"].items():
        print(f"  {k}: {v}")
    print(f"\nCurrent weights:")
    for k, v in opt["current_weights"].items():
        print(f"  {k}: {v}")
    print(f"\nBest metrics: {opt['best_metrics']}")
    print(f"Current metrics: {opt['current_metrics']}")
    print(f"Improvement: {opt['improvement']}")
    print(f"Candidates evaluated: {opt['n_candidates']}")

    with open("docs/weight_optimization.json", "w", encoding="utf-8") as f:
        json.dump(opt, f, indent=2, default=str)
else:
    print("No valid weight combinations found")

print("\nDone.")
