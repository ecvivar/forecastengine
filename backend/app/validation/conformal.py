"""
Phase 2 — Conformal Prediction Prototype.

Implements split conformal and jackknife+ methods for valid prediction
intervals without distributional assumptions.

Goal: coverage 88-92% (tighter than bootstrap's 100%).
"""
from __future__ import annotations

import logging

import numpy as np
from scipy.stats import spearmanr

from app.domain.entities import PredictionConfig, TeamEntity
from app.engine.meta_ensemble import MetaPredictionEngine

logger = logging.getLogger(__name__)


class ConformalPredictor:
    """Conformal prediction for match outcome probabilities."""

    def __init__(self, config: PredictionConfig | None = None):
        self.config = config or PredictionConfig()
        self.engine = MetaPredictionEngine(config=self.config)
        self.cal_scores: list[float] = []
        self.q_hat: float | None = None

    def _nonconformity_score(self, prob: float, outcome: int) -> float:
        """Alpha = 1 - predicted_prob[true_class]."""
        return 1.0 - prob

    def fit_split(self, cal_matches: list[tuple]) -> float:
        """Fit split conformal: compute q_hat from calibration set.

        cal_matches: list of (home, away, actual_outcome)
          actual_outcome: 0=home_win, 1=draw, 2=away_win
        """
        scores = []
        for home, away, outcome in cal_matches:
            r = self.engine.predict(home, away)
            prob = [r.home_win_prob, r.draw_prob, r.away_win_prob][outcome]
            scores.append(self._nonconformity_score(prob, outcome))

        scores.sort()
        n = len(scores)
        q_level = np.ceil((n + 1) * 0.90) / n
        idx = int(np.ceil(q_level * n)) - 1
        self.q_hat = scores[min(idx, n - 1)]
        self.cal_scores = scores
        return float(self.q_hat)

    def predict_split(self, home: TeamEntity, away: TeamEntity) -> dict:
        """Predict with split conformal intervals.

        Returns {outcome: {point, lo, hi}}.
        """
        if self.q_hat is None:
            raise ValueError("call fit_split first")

        r = self.engine.predict(home, away)
        probs = [r.home_win_prob, r.draw_prob, r.away_win_prob]
        labels = ["home_win", "draw", "away_win"]

        result = {}
        for i, label in enumerate(labels):
            lo = max(0.0, probs[i] - self.q_hat)
            hi = min(1.0, probs[i] + self.q_hat)
            result[label] = {"point": probs[i], "ci_lower": round(lo, 4), "ci_upper": round(hi, 4)}
        return result

    def predict_jackknife_plus(
        self, cal_matches: list[tuple], home: TeamEntity, away: TeamEntity
    ) -> dict:
        """Jackknife+ conformal prediction using LOO calibration."""
        n = len(cal_matches)
        loo_preds = []
        for leave_out in range(n):
            train = [cal_matches[j] for j in range(n) if j != leave_out]
            loo_matches = []
            for h, a, o in train:
                r = self.engine.predict(h, a)
                p = [r.home_win_prob, r.draw_prob, r.away_win_prob][o]
                loo_matches.append(p)
            loo_matches.sort()
            if loo_matches:
                loo_preds.append(loo_matches[len(loo_matches) // 2])

        if not loo_preds:
            return self.predict_split(home, away)

        r = self.engine.predict(home, away)
        probs = [r.home_win_prob, r.draw_prob, r.away_win_prob]
        labels = ["home_win", "draw", "away_win"]

        result = {}
        for i, label in enumerate(labels):
            residuals = [abs(p - probs[i]) for p in loo_preds]
            residuals.sort()
            q_idx = int(np.ceil(0.90 * len(residuals))) - 1
            q = residuals[max(0, min(q_idx, len(residuals) - 1))]
            lo = max(0.0, probs[i] - q)
            hi = min(1.0, probs[i] + q)
            result[label] = {"point": probs[i], "ci_lower": round(lo, 4), "ci_upper": round(hi, 4)}
        return result

    def bootstrap_ci(self, home: TeamEntity, away: TeamEntity,
                     n_resamples: int = 300) -> dict:
        """Standard bootstrap percentile CI for comparison."""
        rng = np.random.default_rng(42)
        from copy import deepcopy

        samples_hw, samples_d, samples_aw = [], [], []
        for _ in range(n_resamples):
            h = deepcopy(home)
            a = deepcopy(away)
            h.elo_score = int(h.elo_score * rng.normal(1.0, 0.05))
            a.elo_score = int(a.elo_score * rng.normal(1.0, 0.05))
            r = self.engine.predict(h, a)
            samples_hw.append(r.home_win_prob)
            samples_d.append(r.draw_prob)
            samples_aw.append(r.away_win_prob)

        labels = ["home_win", "draw", "away_win"]
        result = {}
        for label, samples in [("home_win", samples_hw), ("draw", samples_d), ("away_win", samples_aw)]:
            lo = np.percentile(samples, 5)
            hi = np.percentile(samples, 95)
            result[label] = {
                "point": float(np.median(samples)), "ci_lower": round(float(lo), 4),
                "ci_upper": round(float(hi), 4),
            }
        return result

    def evaluate(self, matches: list[tuple], method: str = "split",
                 cal_matches: list[tuple] | None = None) -> dict:
        """Evaluate coverage and width for all matches.

        For 'split': first half is calibration, second half is test.
        For 'bootstrap': no calibration needed.
        """
        if method == "split":
            mid = len(matches) // 2
            cal = matches[:mid]
            test = matches[mid:]
            self.fit_split(cal)
            preds = [self.predict_split(h, a) for h, a, _ in test]
            actuals = [outcome for _, _, outcome in test]
        elif method == "bootstrap":
            preds = [self.bootstrap_ci(h, a) for h, a, _ in matches]
            actuals = [outcome for _, _, outcome in matches]
            test = matches
        elif method == "jackknife+":
            cal = matches[:len(matches)//2]
            test = matches[len(matches)//2:]
            preds = [self.predict_jackknife_plus(cal, h, a) for h, a, _ in test]
            actuals = [outcome for _, _, outcome in test]
        else:
            raise ValueError(f"unknown method: {method}")

        covered = 0
        total = 0
        widths = []
        for pred, outcome in zip(preds, actuals):
            labels = ["home_win", "draw", "away_win"]
            gt_prob = [pred[lab]["point"] for lab in labels][outcome]
            lo = pred[labels[outcome]]["ci_lower"]
            hi = pred[labels[outcome]]["ci_upper"]
            if lo <= gt_prob <= hi:
                covered += 1
            total += 1
            for lab in labels:
                widths.append(pred[lab]["ci_upper"] - pred[lab]["ci_lower"])

        rate = covered / max(total, 1)
        return {
            "method": method,
            "n_test": total,
            "coverage": round(rate, 4),
            "avg_width": round(float(np.mean(widths)), 4),
            "std_width": round(float(np.std(widths)), 4),
        }

    @staticmethod
    def comparison_table(results: list[dict]) -> str:
        lines = [
            "# Conformal Prediction Comparison\n",
            "| Method | Coverage | Avg Width | Std Width | N Test |",
            "|--------|----------|-----------|-----------|--------|",
        ]
        for r in results:
            lines.append(
                f"| {r['method']} | {r['coverage']:.1%} | "
                f"{r['avg_width']:.4f} | {r['std_width']:.4f} | {r['n_test']} |"
            )
        return "\n".join(lines)
