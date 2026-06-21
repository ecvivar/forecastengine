"""
Phase 8 — Uncertainty Consistency Audit.
Validates that higher uncertainty -> wider CIs and vice versa.
"""
import numpy as np
from copy import deepcopy
from scipy.stats import pearsonr, spearmanr
from app.domain.entities import PredictionConfig, TeamEntity
from app.engine.meta_ensemble import MetaPredictionEngine
from app.engine.match_prediction import MatchPredictionEngine


class UncertaintyConsistency:
    """Measure correlation between prediction uncertainty and CI width."""

    def __init__(self, config: PredictionConfig | None = None):
        self.config = config or PredictionConfig()
        self.ensemble = MetaPredictionEngine(config=self.config)
        self.engine = MatchPredictionEngine(config=self.config)

    def _team_uncertainty(self, team: TeamEntity) -> float:
        """Uncertainty as entropy over skills / rating deviation."""
        ts = self.engine.compute_team_strength(team)
        return float(ts.uncertainty) if hasattr(ts, "uncertainty") else 0.01

    def _ci_width(self, home: TeamEntity, away: TeamEntity,
                  n_resamples: int = 200, noise_scale: float = 0.10) -> float:
        """Bootstrap the prediction and measure CI width for home_win_prob."""
        rng = np.random.default_rng(42)
        samples = []
        for _ in range(n_resamples):
            h = deepcopy(home)
            a = deepcopy(away)
            h.elo_score = int(h.elo_score * rng.normal(1.0, noise_scale))
            a.elo_score = int(a.elo_score * rng.normal(1.0, noise_scale))
            if h.xg_for: h.xg_for *= rng.normal(1.0, noise_scale * 0.5)
            if a.xg_for: a.xg_for *= rng.normal(1.0, noise_scale * 0.5)
            if h.xg_against: h.xg_against *= rng.normal(1.0, noise_scale * 0.5)
            if a.xg_against: a.xg_against *= rng.normal(1.0, noise_scale * 0.5)
            h.fifa_rank = max(1, int((h.fifa_rank or 50) * rng.normal(1.0, noise_scale * 0.3)))
            a.fifa_rank = max(1, int((a.fifa_rank or 50) * rng.normal(1.0, noise_scale * 0.3)))
            r = self.ensemble.predict(h, a)
            samples.append(r.home_win_prob)
        lo = np.percentile(samples, 5)
        hi = np.percentile(samples, 95)
        return float(hi - lo)

    def _match_entropy(self, home: TeamEntity, away: TeamEntity) -> float:
        """Prediction entropy — higher = more uncertain."""
        r = self.ensemble.predict(home, away)
        p = np.array([r.home_win_prob, r.draw_prob, r.away_win_prob])
        p = np.clip(p, 1e-10, 1)
        return float(-np.sum(p * np.log(p)))

    def _match_spread(self, home: TeamEntity, away: TeamEntity) -> float:
        """Uncertainty proxy: 1 - |home_win - away_win|. Higher = more uncertain."""
        r = self.ensemble.predict(home, away)
        spread = abs(r.home_win_prob - r.away_win_prob)
        return 1.0 - float(spread)

    def audit(self, match_pairs: list, n_resamples: int = 200) -> dict:
        uncertainties = []
        ci_widths = []
        entropies = []
        for home, away, _ in match_pairs:
            u = self._match_spread(home, away)
            w = self._ci_width(home, away, n_resamples)
            e = self._match_entropy(home, away)
            uncertainties.append(u)
            ci_widths.append(w)
            entropies.append(e)

        u_arr = np.array(uncertainties)
        w_arr = np.array(ci_widths)
        e_arr = np.array(entropies)

        pw_c, _ = spearmanr(u_arr, w_arr)
        pe_c, _ = spearmanr(e_arr, w_arr)
        pu_c, _ = spearmanr(u_arr, e_arr)

        return {
            "n_matches": len(match_pairs),
            "mean_uncertainty": round(float(np.mean(u_arr)), 4),
            "std_uncertainty": round(float(np.std(u_arr)), 4),
            "mean_ci_width": round(float(np.mean(w_arr)), 4),
            "std_ci_width": round(float(np.std(w_arr)), 4),
            "mean_entropy": round(float(np.mean(e_arr)), 4),
            "corr_uncertainty_width": round(float(pw_c), 4),
            "corr_entropy_width": round(float(pe_c), 4),
            "corr_uncertainty_entropy": round(float(pu_c), 4),
            "passes": float(pw_c) > 0.70,
            "interpretation": self._interpret(pw_c, pe_c),
        }

    def _interpret(self, u_w_corr: float, e_w_corr: float) -> str:
        if u_w_corr > 0.80 and e_w_corr > 0.80:
            return "Excellent - strong internal consistency."
        elif u_w_corr > 0.70 and e_w_corr > 0.70:
            return "Good - uncertainty aligns with CI width."
        elif u_w_corr > 0.50:
            return "Adequate - moderate alignment."
        else:
            return "Weak - uncertainty and CI width are poorly aligned."

    @staticmethod
    def summary_table(result: dict) -> str:
        lines = [
            "# Uncertainty Consistency Audit\n",
            f"**Sample Size:** {result['n_matches']} matches\n",
            f"- **Mean Uncertainty:** {result['mean_uncertainty']:.4f} (std={result['std_uncertainty']:.4f})",
            f"- **Mean CI Width:** {result['mean_ci_width']:.4f} (std={result['std_ci_width']:.4f})",
            f"- **Mean Entropy:** {result['mean_entropy']:.4f}",
            "",
            "## Correlations",
            f"- **Spearman(Uncertainty, CI Width):** {result['corr_uncertainty_width']:.4f}",
            f"- **Spearman(Entropy, CI Width):** {result['corr_entropy_width']:.4f}",
            f"- **Spearman(Uncertainty, Entropy):** {result['corr_uncertainty_entropy']:.4f}",
            "",
            f"**Target:** Correlation > 0.70 -> **{'PASS' if result['passes'] else 'FAIL'}**",
            f"**Interpretation:** {result['interpretation']}",
        ]
        return "\n".join(lines)
