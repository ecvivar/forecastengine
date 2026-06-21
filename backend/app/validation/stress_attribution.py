"""
Phase 1 — Stress Variance Attribution.
Decomposes prediction variance by individual signal sources.
"""
import numpy as np
from copy import deepcopy
from app.domain.entities import PredictionConfig, TeamEntity
from app.engine.match_prediction import MatchPredictionEngine
from app.engine.meta_ensemble import MetaPredictionEngine


class StressAttribution:
    """Decompose prediction variance across signal sources."""

    def __init__(self, config: PredictionConfig | None = None):
        self.config = config or PredictionConfig()
        self.engine = MetaPredictionEngine(config=self.config)

    def _vary_signal(self, home: TeamEntity, away: TeamEntity,
                     signal: str, n: int = 300) -> np.ndarray:
        """Perturb ONE signal; keep others fixed. Return home_win_probs."""
        results = []
        rng = np.random.default_rng(42)
        for _ in range(n):
            h = deepcopy(home)
            a = deepcopy(away)
            if signal == "elo":
                h.elo_score = int(h.elo_score * rng.uniform(0.85, 1.15))
                a.elo_score = int(a.elo_score * rng.uniform(0.85, 1.15))
            elif signal == "xg_attack":
                h.xg_for = (h.xg_for or 1.5) * rng.uniform(0.80, 1.20)
                a.xg_for = (a.xg_for or 1.5) * rng.uniform(0.80, 1.20)
            elif signal == "xg_defense":
                h.xg_against = (h.xg_against or 1.5) * rng.uniform(0.80, 1.20)
                a.xg_against = (a.xg_against or 1.5) * rng.uniform(0.80, 1.20)
            elif signal == "fifa":
                h.fifa_rank = max(1, int((h.fifa_rank or 50) * rng.uniform(0.8, 1.2)))
                a.fifa_rank = max(1, int((a.fifa_rank or 50) * rng.uniform(0.8, 1.2)))
            elif signal == "home_advantage":
                ha = bool(rng.choice([True, False]))
                r = self.engine.predict(h, a, home_advantage=ha)
            elif signal == "bayesian_prior":
                cfg = deepcopy(self.config)
                cfg.bayesian_prior_strength = rng.uniform(0.0, 1.0)
                eng = MetaPredictionEngine(config=cfg)
                r = eng.predict(h, a)
            elif signal == "poisson_model":
                cfg = deepcopy(self.config)
                cfg.dixon_coles_tau = 0.0
                eng = MetaPredictionEngine(config=cfg)
                r = eng.predict(h, a)
            elif signal == "strength_diff":
                w = {m: 0.25 for m in MetaPredictionEngine.MODEL_NAMES}
                w["strength_diff"] = rng.uniform(0.05, 0.50)
                eng = MetaPredictionEngine(config=self.config, weights=w)
                r = eng.predict(h, a)
            elif signal == "dixon_coles":
                cfg = deepcopy(self.config)
                cfg.dixon_coles_tau = rng.uniform(0.0, 0.05)
                eng = MetaPredictionEngine(config=cfg)
                r = eng.predict(h, a)
            elif signal == "ensemble_weights":
                w = {}
                for m in MetaPredictionEngine.MODEL_NAMES:
                    w[m] = rng.uniform(0.05, 0.50)
                total = sum(w.values())
                w = {k: v / total for k, v in w.items()}
                eng = MetaPredictionEngine(config=self.config, weights=w)
                r = eng.predict(h, a)
            if signal not in ("home_advantage", "bayesian_prior", "poisson_model",
                              "strength_diff", "dixon_coles", "ensemble_weights"):
                r = self.engine.predict(h, a)
            results.append(r.home_win_prob)
        return np.array(results)

    def analyze(self, home: TeamEntity, away: TeamEntity,
                n: int = 300) -> dict:
        signals = [
            "elo", "xg_attack", "xg_defense", "fifa", "home_advantage",
            "bayesian_prior", "poisson_model", "strength_diff",
            "dixon_coles", "ensemble_weights",
        ]
        baseline = self.engine.predict(home, away)
        base_hw = baseline.home_win_prob

        # Perturb ALL signals simultaneously for total variance
        rng_all = np.random.default_rng(99)
        all_results = []
        for _ in range(n):
            h = deepcopy(home); a = deepcopy(away)
            h.elo_score = int(h.elo_score * rng_all.uniform(0.85, 1.15))
            a.elo_score = int(a.elo_score * rng_all.uniform(0.85, 1.15))
            if h.xg_for: h.xg_for *= rng_all.uniform(0.80, 1.20)
            if a.xg_for: a.xg_for *= rng_all.uniform(0.80, 1.20)
            if h.xg_against: h.xg_against *= rng_all.uniform(0.80, 1.20)
            if a.xg_against: a.xg_against *= rng_all.uniform(0.80, 1.20)
            h.fifa_rank = max(1, int((h.fifa_rank or 50) * rng_all.uniform(0.8, 1.2)))
            a.fifa_rank = max(1, int((a.fifa_rank or 50) * rng_all.uniform(0.8, 1.2)))
            r = self.engine.predict(h, a)
            all_results.append(r.home_win_prob)
        var_total = float(np.var(all_results))

        attributions = []
        for sig in signals:
            vals = self._vary_signal(home, away, sig, n)
            var_partial = float(np.var(vals))
            # Contribution: how much of total variance is explained by this signal alone
            # Clamp to 0-100% (values >100% mean other signals cancel this one's effect)
            pct = min(100.0, (var_partial / var_total * 100)) if var_total > 0 else 0.0
            attributions.append({
                "signal": sig,
                "var_partial": round(var_partial, 6),
                "var_pct": round(pct, 2),
                "mean": round(float(np.mean(vals)), 4),
                "std": round(float(np.std(vals)), 4),
            })

        attributions.sort(key=lambda x: -x["var_pct"])
        return {
            "baseline_home_win": round(base_hw, 4),
            "var_total": round(var_total, 6),
            "n_per_signal": n,
            "attributions": attributions,
        }

    def summary_table(self, result: dict) -> str:
        lines = ["| Signal | Var Partial | % Contrib | Mean | Std |"]
        lines.append("|--------|-------------|-----------|------|-----|")
        for a in result["attributions"]:
            lines.append(f"| {a['signal']} | {a['var_partial']:.6f} | {a['var_pct']:.1f}% | {a['mean']:.4f} | {a['std']:.4f} |")
        lines.append(f"\n**Total Variance:** {result['var_total']:.6f}")
        lines.append(f"**Baseline HW:** {result['baseline_home_win']:.4f}")
        return "\n".join(lines)
