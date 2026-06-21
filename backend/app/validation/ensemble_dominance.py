"""
Phase 2 — Ensemble Dominance Audit.
Measures whether the ensemble truly uses 4 models or concentrates on fewer.
"""
import numpy as np
from scipy.stats import entropy
from app.domain.entities import PredictionConfig
from app.engine.meta_ensemble import MetaPredictionEngine
from app.engine.match_prediction import MatchPredictionEngine


class EnsembleDominance:
    """Analyze ensemble weight distribution and effective model count."""

    MODEL_NAMES = MetaPredictionEngine.MODEL_NAMES

    def __init__(self, config: PredictionConfig | None = None):
        self.config = config or PredictionConfig()
        self.ensemble = MetaPredictionEngine(config=self.config)

    def effective_models(self, weights: dict[str, float]) -> float:
        w = np.array(list(weights.values()))
        w = w / w.sum()
        ent = entropy(w)
        return float(np.exp(ent))

    def analyze_current(self) -> dict:
        w = self.ensemble.weights
        w_arr = np.array(list(w.values()))
        w_arr = w_arr / w_arr.sum()
        ent = entropy(w_arr)
        eff = np.exp(ent)
        return {
            "weights": {k: round(v, 4) for k, v in w.items()},
            "weight_mean": round(float(np.mean(w_arr)), 4),
            "weight_variance": round(float(np.var(w_arr)), 6),
            "entropy": round(float(ent), 4),
            "effective_models": round(float(eff), 4),
            "max_weight": round(float(np.max(w_arr)), 4),
            "min_weight": round(float(np.min(w_arr)), 4),
        }

    def dominance_ratio(self) -> float:
        w = np.array(list(self.ensemble.weights.values()))
        w = w / w.sum()
        top2 = sum(sorted(w, reverse=True)[:2])
        return float(top2)

    def simulate_weight_distributions(self, n: int = 10000) -> dict:
        rng = np.random.default_rng(42)
        effs = []
        for _ in range(n):
            w = rng.uniform(0.05, 0.50, size=4)
            w = w / w.sum()
            effs.append(float(np.exp(entropy(w))))
        return {
            "mean_effective": round(float(np.mean(effs)), 4),
            "std_effective": round(float(np.std(effs)), 4),
            "p5": round(float(np.percentile(effs, 5)), 4),
            "p95": round(float(np.percentile(effs, 95)), 4),
            "min_possible": round(float(min(effs)), 4),
            "max_possible": round(float(max(effs)), 4),
        }

    def full_report(self) -> dict:
        current = self.analyze_current()
        sim = self.simulate_weight_distributions()
        dr = self.dominance_ratio()
        return {
            "current": current,
            "dominance_ratio": round(dr, 4),
            "simulation": sim,
            "interpretation": self._interpret(current, dr),
        }

    def _interpret(self, current: dict, dr: float) -> str:
        if current["effective_models"] >= 3.5:
            return "Excellent - all 4 models contribute meaningfully."
        elif current["effective_models"] >= 3.0:
            return "Good - ensemble uses ~3 effective models."
        elif current["effective_models"] >= 2.5:
            return "Adequate - ensemble uses ~2-3 effective models."
        elif current["effective_models"] >= 2.0:
            return "Marginal - effectively a 2-model ensemble."
        else:
            return "Poor - effectively a 1-2 model ensemble."

    @staticmethod
    def summary_table(report: dict) -> str:
        c = report["current"]
        lines = [
            "# Ensemble Dominance Report\n",
            "## Current Weights\n",
            "| Model | Weight |",
            "|-------|--------|",
        ]
        for m, w in c["weights"].items():
            lines.append(f"| {m} | {w:.4f} |")
        lines.extend([
            f"\n- **Effective Models:** {c['effective_models']:.2f}",
            f"- **Entropy:** {c['entropy']:.4f}",
            f"- **Weight Variance:** {c['weight_variance']:.6f}",
            f"- **Dominance Ratio (Top2):** {report['dominance_ratio']:.2%}",
            f"\n## Simulation (n={report['simulation'].get('mean_effective', 0)*0:,.0f} random draws)",
            f"- **Mean effective:** {report['simulation']['mean_effective']:.2f}",
            f"- **95% range:** [{report['simulation']['p5']:.2f}, {report['simulation']['p95']:.2f}]",
            f"\n**Interpretation:** {report['interpretation']}",
        ])
        return "\n".join(lines)
