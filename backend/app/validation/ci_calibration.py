"""
FASE 4 — Confidence Interval Recalibration.

Tests three bootstrap methods: Percentile, BCa, Studentized.
Goal: achieve 85-95% coverage for nominal 90% CI.
"""
from __future__ import annotations

import logging
from copy import deepcopy

logger = logging.getLogger(__name__)

import numpy as np

from app.domain.entities import PredictionConfig, TeamEntity
from app.engine.meta_ensemble import MetaPredictionEngine

logger = logging.getLogger(__name__)


class CIRecalibrator:
    """Test and compare CI methods for coverage calibration."""

    def __init__(self, config: PredictionConfig | None = None):
        self.config = config or PredictionConfig()
        self.engine = MetaPredictionEngine(config=self.config)

    def _resample(self, home: TeamEntity, away: TeamEntity, n: int,
                  home_advantage: bool = True) -> np.ndarray:
        """Generate n resampled predictions by perturbing weights + signals."""
        probs = []
        for _ in range(n):
            h = deepcopy(home)
            a = deepcopy(away)
            rd = getattr(h, 'rating_deviation', None) or 50.0
            ns = max(0.05, rd / 100.0)
            h.elo_score = int(h.elo_score * np.random.normal(1.0, ns * 0.1))
            if h.xg_for:
                h.xg_for *= np.random.normal(1.0, ns * 0.15)
            if h.xg_against:
                h.xg_against *= np.random.normal(1.0, ns * 0.15)
            a.elo_score = int(a.elo_score * np.random.normal(1.0, ns * 0.1))
            if a.xg_for:
                a.xg_for *= np.random.normal(1.0, ns * 0.15)
            if a.xg_against:
                a.xg_against *= np.random.normal(1.0, ns * 0.15)

            r = self.engine.predict(h, a, home_advantage)
            probs.append([r.home_win_prob, r.draw_prob, r.away_win_prob])
        return np.array(probs)

    def percentile_ci(self, samples: np.ndarray, alpha: float = 0.10) -> dict:
        """Standard percentile bootstrap."""
        lower = np.percentile(samples, alpha / 2 * 100, axis=0)
        upper = np.percentile(samples, (1 - alpha / 2) * 100, axis=0)
        return {"lower": lower, "upper": upper}

    def bca_ci(self, samples: np.ndarray, point: np.ndarray, alpha: float = 0.10) -> dict:
        """BCa bootstrap (bias-corrected and accelerated)."""
        n = len(samples)
        # Bias correction
        z0 = np.zeros(3)
        for i in range(3):
            p_hat = np.mean(samples[:, i] < point[i])
            from scipy.stats import norm
            z0[i] = norm.ppf(p_hat)

        # Acceleration (jackknife)
        jack = np.zeros((n, 3))
        for j in range(n):
            jack[j] = np.mean(np.delete(samples, j, axis=0), axis=0)
        jack_center = np.mean(jack, axis=0)
        num = np.sum((jack_center - jack) ** 3, axis=0)
        den = np.sum((jack_center - jack) ** 2, axis=0) ** 1.5
        a = np.where(den > 0, num / (6 * den), 0)

        from scipy.stats import norm
        z_alpha = norm.ppf(alpha / 2)
        z_1malpha = norm.ppf(1 - alpha / 2)

        lower = np.zeros(3)
        upper = np.zeros(3)
        for i in range(3):
            # Adjust percentiles
            def _adj(z):
                return norm.cdf(z0[i] + (z0[i] + z) / (1 - a[i] * (z0[i] + z)))
            p_lo = _adj(z_alpha)
            p_hi = _adj(z_1malpha)
            lower[i] = np.percentile(samples[:, i], p_lo * 100)
            upper[i] = np.percentile(samples[:, i], p_hi * 100)

        return {"lower": lower.clip(0, 1), "upper": upper.clip(0, 1)}

    def studentized_ci(self, samples: np.ndarray, point: np.ndarray,
                       alpha: float = 0.10) -> dict:
        """Studentized bootstrap using bootstrap SE."""
        n = len(samples)
        lower = np.zeros(3)
        upper = np.zeros(3)
        for i in range(3):
            se = np.std(samples[:, i]) / np.sqrt(n)
            # Bootstrap t percentiles
            t_vals = (samples[:, i] - point[i]) / max(se, 1e-10)
            t_sorted = sorted(t_vals)
            t_lo = t_sorted[int(alpha / 2 * n)]
            t_hi = t_sorted[int((1 - alpha / 2) * n)]
            lower[i] = point[i] - t_hi * se
            upper[i] = point[i] - t_lo * se
        return {"lower": lower.clip(0, 1), "upper": upper.clip(0, 1)}

    def evaluate(self, match_pairs: list[tuple], n_resamples: int = 500) -> dict:
        """Evaluate all three CI methods on match pairs."""
        methods = {"percentile": self.percentile_ci,
                   "bca": self.bca_ci,
                   "studentized": self.studentized_ci}
        results = {}

        for method_name, method_fn in methods.items():
            covered = 0
            total = 0
            widths = []

            for home, away, outcome in match_pairs:
                point_r = self.engine.predict(home, away)
                point = np.array([point_r.home_win_prob, point_r.draw_prob, point_r.away_win_prob])
                samples = self._resample(home, away, n_resamples)
                try:
                    ci = method_fn(samples, point)
                except Exception as e:
                    logger.warning(f"{method_name} failed: {e}")
                    continue

                lo = np.asarray(ci["lower"]).ravel()
                hi = np.asarray(ci["upper"]).ravel()
                if lo.shape != (3,) or hi.shape != (3,):
                    continue

                total += 3
                for i in range(3):
                    width = float(hi[i]) - float(lo[i])
                    widths.append(width)
                    if float(lo[i]) <= float(point[i]) <= float(hi[i]):
                        covered += 1

            rate = covered / max(total, 1)
            passes = 0.85 <= rate <= 0.95
            results[method_name] = {
                "coverage_rate": round(rate, 4),
                "avg_ci_width": round(float(np.mean(widths)), 4) if widths else 0,
                "ci_width_std": round(float(np.std(widths)), 4) if widths else 0,
                "passes": bool(passes),
            }

        return results
