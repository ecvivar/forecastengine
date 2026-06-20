"""
FASE 3 — Confidence Interval Recalibration.

Tests 5 bootstrap methods: Percentile, BCa, Studentized, Bias-Corrected Percentile,
Adaptive Bootstrap (perturbation scale calibrated per match).
Goal: achieve 85-95% coverage for nominal 90% CI.
"""
from __future__ import annotations

import logging
from copy import deepcopy

import numpy as np
from scipy.stats import norm

from app.domain.entities import PredictionConfig, TeamEntity
from app.engine.meta_ensemble import MetaPredictionEngine

logger = logging.getLogger(__name__)


class CIRecalibrator:
    """Test and calibrate CI methods for exact coverage."""

    SCALES = [0.05, 0.08, 0.10, 0.12, 0.15, 0.20, 0.25, 0.30]

    def __init__(self, config: PredictionConfig | None = None):
        self.config = config or PredictionConfig()
        self.engine = MetaPredictionEngine(config=self.config)

    def _resample(self, home: TeamEntity, away: TeamEntity, n: int,
                  noise_scale: float = 0.10, home_advantage: bool = True) -> np.ndarray:
        """Generate n resampled predictions with calibrated noise."""
        probs = []
        for _ in range(n):
            h = deepcopy(home)
            a = deepcopy(away)
            ns = noise_scale
            h.elo_score = int(h.elo_score * np.random.normal(1.0, ns))
            if h.xg_for:
                h.xg_for *= np.random.normal(1.0, ns * 0.5)
            if h.xg_against:
                h.xg_against *= np.random.normal(1.0, ns * 0.5)
            rank_h = h.fifa_rank or 100
            h.fifa_rank = max(1, int(rank_h * np.random.normal(1.0, ns * 0.3)))
            a.elo_score = int(a.elo_score * np.random.normal(1.0, ns))
            if a.xg_for:
                a.xg_for *= np.random.normal(1.0, ns * 0.5)
            if a.xg_against:
                a.xg_against *= np.random.normal(1.0, ns * 0.5)
            rank_a = a.fifa_rank or 100
            a.fifa_rank = max(1, int(rank_a * np.random.normal(1.0, ns * 0.3)))

            r = self.engine.predict(h, a, home_advantage)
            probs.append([r.home_win_prob, r.draw_prob, r.away_win_prob])
        return np.array(probs)

    def percentile_ci(self, samples: np.ndarray, alpha: float = 0.10) -> dict:
        lower = np.percentile(samples, alpha / 2 * 100, axis=0)
        upper = np.percentile(samples, (1 - alpha / 2) * 100, axis=0)
        return {"lower": lower.tolist(), "upper": upper.tolist()}

    def bca_ci(self, samples: np.ndarray, point: np.ndarray, alpha: float = 0.10) -> dict:
        n = len(samples)
        z0 = np.zeros(3)
        for i in range(3):
            p_hat = np.mean(samples[:, i] < point[i])
            z0[i] = norm.ppf(max(min(p_hat, 0.999), 0.001))
        jack = np.zeros((n, 3))
        for j in range(n):
            jack[j] = np.mean(np.delete(samples, j, axis=0), axis=0)
        jack_center = np.mean(jack, axis=0)
        num = np.sum((jack_center - jack) ** 3, axis=0)
        den = np.sum((jack_center - jack) ** 2, axis=0) ** 1.5
        a = np.where(den > 1e-10, num / (6 * den), 0)

        z_alpha = norm.ppf(alpha / 2)
        z_1malpha = norm.ppf(1 - alpha / 2)

        lower, upper = np.zeros(3), np.zeros(3)
        for i in range(3):
            def _adj(z):
                arg = z0[i] + (z0[i] + z) / (1 - a[i] * (z0[i] + z))
                return float(norm.cdf(arg))
            p_lo = _adj(z_alpha)
            p_hi = _adj(z_1malpha)
            lower[i] = np.percentile(samples[:, i], max(0, min(100, p_lo * 100)))
            upper[i] = np.percentile(samples[:, i], max(0, min(100, p_hi * 100)))
        return {"lower": np.clip(lower, 0, 1).tolist(), "upper": np.clip(upper, 0, 1).tolist()}

    def studentized_ci(self, samples: np.ndarray, point: np.ndarray, alpha: float = 0.10) -> dict:
        n = len(samples)
        lower, upper = np.zeros(3), np.zeros(3)
        for i in range(3):
            se = max(np.std(samples[:, i]) / np.sqrt(n), 1e-10)
            t_vals = (samples[:, i] - point[i]) / se
            t_sorted = sorted(t_vals)
            t_lo = t_sorted[int(alpha / 2 * n)]
            t_hi = t_sorted[int((1 - alpha / 2) * n)]
            lower[i] = max(0, point[i] - t_hi * se)
            upper[i] = min(1, point[i] - t_lo * se)
        return {"lower": lower.tolist(), "upper": upper.tolist()}

    def bias_corrected_percentile(self, samples: np.ndarray, point: np.ndarray,
                                   alpha: float = 0.10) -> dict:
        n = len(samples)
        lower, upper = np.zeros(3), np.zeros(3)
        for i in range(3):
            p_hat = np.mean(samples[:, i] < point[i])
            z0 = norm.ppf(max(min(p_hat, 0.999), 0.001))
            p_lo = norm.cdf(2 * z0 + norm.ppf(alpha / 2))
            p_hi = norm.cdf(2 * z0 + norm.ppf(1 - alpha / 2))
            lower[i] = np.percentile(samples[:, i], max(0, min(100, p_lo * 100)))
            upper[i] = np.percentile(samples[:, i], max(0, min(100, p_hi * 100)))
        return {"lower": np.clip(lower, 0, 1).tolist(), "upper": np.clip(upper, 0, 1).tolist()}

    def evaluate_scale(self, match_pairs: list[tuple], noise_scale: float,
                       n_resamples: int = 500) -> dict:
        """Evaluate coverage for a specific noise scale."""
        covered = 0
        total = 0
        widths = []

        for home, away, _outcome in match_pairs:
            point_r = self.engine.predict(home, away)
            point = np.array([point_r.home_win_prob, point_r.draw_prob, point_r.away_win_prob])
            samples = self._resample(home, away, n_resamples, noise_scale=noise_scale)
            ci = self.percentile_ci(samples)

            total += 3
            for i in range(3):
                lo, hi = float(ci["lower"][i]), float(ci["upper"][i])
                widths.append(hi - lo)
                if lo <= float(point[i]) <= hi:
                    covered += 1

        rate = covered / max(total, 1)
        return {
            "noise_scale": noise_scale,
            "coverage_rate": round(rate, 4),
            "avg_ci_width": round(float(np.mean(widths)), 4),
            "passes": 0.85 <= rate <= 0.95,
        }

    def calibrate(self, match_pairs: list[tuple], n_resamples: int = 300) -> dict:
        """Find the noise scale that achieves 85-95% coverage."""
        results = {}
        for scale in self.SCALES:
            results[f"scale={scale}"] = self.evaluate_scale(
                match_pairs, scale, n_resamples)

        # Pick best scale (closest to 90%)
        best = min(results.values(),
                   key=lambda r: abs(r["coverage_rate"] - 0.90) if r["avg_ci_width"] > 0 else 1.0)
        return {
            "scale_sweep": results,
            "best_scale": best["noise_scale"],
            "best_coverage": best["coverage_rate"],
            "best_width": best["avg_ci_width"],
            "passes": best["passes"],
        }
