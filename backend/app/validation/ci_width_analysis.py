"""
Phase 4 — Confidence Interval Width Analysis.
Compares CI methods: Bootstrap, BCa, Adaptive Bootstrap, Studentized.
"""
import numpy as np
from copy import deepcopy
from scipy.stats import norm
from app.domain.entities import PredictionConfig, TeamEntity
from app.engine.meta_ensemble import MetaPredictionEngine


class CIWidthAnalysis:
    """Analyze CI coverage vs width across methods."""

    METHODS = ["percentile", "bca", "studentized", "adaptive"]

    def __init__(self, config: PredictionConfig | None = None):
        self.config = config or PredictionConfig()
        self.engine = MetaPredictionEngine(config=self.config)

    def _resample(self, home: TeamEntity, away: TeamEntity,
                  n: int, noise_scale: float = 0.10) -> np.ndarray:
        rng = np.random.default_rng(42)
        samples = []
        for _ in range(n):
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
            r = self.engine.predict(h, a)
            samples.append(r.home_win_prob)
        return np.array(samples)

    def percentile_ci(self, samples: np.ndarray, alpha: float = 0.10) -> tuple:
        lo = np.percentile(samples, alpha / 2 * 100)
        hi = np.percentile(samples, (1 - alpha / 2) * 100)
        return float(lo), float(hi)

    def bca_ci(self, samples: np.ndarray, point: float, alpha: float = 0.10) -> tuple:
        n = len(samples)
        z0 = norm.ppf(np.mean(samples < point))
        jack = np.array([np.mean(np.delete(samples, i)) for i in range(n)])
        jack_mean = np.mean(jack)
        num = np.sum((jack_mean - jack) ** 3)
        den = np.sum((jack_mean - jack) ** 2) ** 1.5
        a = num / (6 * den) if den > 0 else 0
        z_alpha = norm.ppf(alpha / 2)
        adj_l = norm.cdf(z0 + (z0 + z_alpha) / (1 - a * (z0 + z_alpha)))
        adj_u = norm.cdf(z0 + (z0 - z_alpha) / (1 - a * (z0 - z_alpha)))
        lo = np.percentile(samples, adj_l * 100)
        hi = np.percentile(samples, adj_u * 100)
        return float(lo), float(hi)

    def studentized_ci(self, samples: np.ndarray, point: float, alpha: float = 0.10) -> tuple:
        se = float(np.std(samples)) / max(np.sqrt(len(samples)), 1)
        t_vals = (samples - point) / max(se, 1e-8)
        t_lo = np.percentile(t_vals, alpha / 2 * 100)
        t_hi = np.percentile(t_vals, (1 - alpha / 2) * 100)
        return point - t_hi * se, point - t_lo * se

    def adaptive_ci(self, samples: np.ndarray, point: float, alpha: float = 0.10) -> tuple:
        n = len(samples)
        k = max(1, int(n * (1 - alpha)))
        sorted_s = np.sort(samples)
        widths = sorted_s[k:] - sorted_s[:n - k]
        best = int(np.argmin(widths))
        lo = sorted_s[best]
        hi = sorted_s[best + k]
        return float(lo), float(hi)

    def evaluate_method(self, match_pairs: list, method: str,
                        alpha: float = 0.10, noise_scale: float = 0.10,
                        n_resamples: int = 500) -> dict:
        cover_count = 0
        widths = []
        total = len(match_pairs)
        for home, away, outcome in match_pairs:
            r = self.engine.predict(home, away)
            point = r.home_win_prob
            samps = self._resample(home, away, n_resamples, noise_scale)
            if method == "percentile":
                lo, hi = self.percentile_ci(samps, alpha)
            elif method == "bca":
                lo, hi = self.bca_ci(samps, point, alpha)
            elif method == "studentized":
                lo, hi = self.studentized_ci(samps, point, alpha)
            elif method == "adaptive":
                lo, hi = self.adaptive_ci(samps, point, alpha)
            else:
                lo, hi = self.percentile_ci(samps, alpha)
            widths.append(hi - lo)
            if lo <= point <= hi:
                cover_count += 1
        coverage = cover_count / max(total, 1)
        return {
            "method": method,
            "alpha": alpha,
            "nominal_coverage": 1 - alpha,
            "observed_coverage": round(coverage, 4),
            "avg_width": round(float(np.mean(widths)), 4),
            "std_width": round(float(np.std(widths)), 4),
            "n_matches": total,
        }

    def compare_methods(self, match_pairs: list, alphas: list[float] | None = None,
                        noise_scale: float = 0.10, n_resamples: int = 500) -> list[dict]:
        if alphas is None:
            alphas = [0.20, 0.10, 0.05]
        all_results = []
        for alpha in alphas:
            for method in self.METHODS:
                r = self.evaluate_method(match_pairs, method, alpha, noise_scale, n_resamples)
                all_results.append(r)
        return all_results

    @staticmethod
    def summary_table(results: list[dict]) -> str:
        lines = ["# CI Width Analysis\n", "| Method | Alpha | Nominal | Observed Coverage | Avg Width | Std Width |",
                 "|--------|-------|---------|-------------------|-----------|-----------|"]
        for r in results:
            lines.append(f"| {r['method']} | {r['alpha']:.2f} | {r['nominal_coverage']:.0%} | "
                         f"{r['observed_coverage']:.2%} | {r['avg_width']:.4f} | {r['std_width']:.4f} |")
        return "\n".join(lines)

    @staticmethod
    def coverage_curve_data(results: list[dict]) -> list[dict]:
        curve = {}
        for r in results:
            key = r["method"]
            if key not in curve:
                curve[key] = []
            curve[key].append({
                "nominal": r["nominal_coverage"],
                "observed": r["observed_coverage"],
                "width": r["avg_width"],
            })
        output = []
        for method, points in curve.items():
            output.append({"method": method, "points": points})
        return output
