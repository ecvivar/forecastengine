"""
FASE 5 — Reliability Diagrams.

Groups predicted probabilities into 10 bins (0-10%, 10-20%, ..., 90-100%),
measures predicted vs observed frequency, computes ECE, MCE, per-bin errors.
"""
from __future__ import annotations

import logging

import numpy as np

from app.validation.calibration_metrics import CalibrationMetrics

logger = logging.getLogger(__name__)


class ReliabilityAnalyzer:
    """Compute reliability (calibration curve) for predicted probabilities."""

    def __init__(self, n_bins: int = 10):
        self.n_bins = n_bins

    def analyze(self, probs: np.ndarray, outcomes: np.ndarray) -> dict:
        """
        probs: (n_matches, 3) — [home_win, draw, away_win]
        outcomes: (n_matches, 3) — one-hot
        Returns per-bin calibration and aggregate metrics.
        """
        results = {}
        labels = ["home_win", "draw", "away_win"]

        for i, label in enumerate(labels):
            p = probs[:, i]
            o = outcomes[:, i]
            bin_edges = np.linspace(0, 1, self.n_bins + 1)
            bins = np.digitize(p, bin_edges[1:-1])  # 0..(n_bins-1)

            bin_data = []
            for b in range(self.n_bins):
                mask = bins == b
                count = int(np.sum(mask))
                if count == 0:
                    bin_data.append({
                        "bin": f"{bin_edges[b]*100:.0f}-{bin_edges[b+1]*100:.0f}%",
                        "count": 0,
                        "predicted_freq": round(float(bin_edges[b] + 0.5 * (bin_edges[b+1] - bin_edges[b])), 4),
                        "observed_freq": 0.0,
                        "error": 0.0,
                        "abs_error": 0.0,
                    })
                    continue
                pred_freq = float(np.mean(p[mask]))
                obs_freq = float(np.mean(o[mask]))
                bin_data.append({
                    "bin": f"{bin_edges[b]*100:.0f}-{bin_edges[b+1]*100:.0f}%",
                    "count": count,
                    "predicted_freq": round(pred_freq, 4),
                    "observed_freq": round(obs_freq, 4),
                    "error": round(obs_freq - pred_freq, 4),
                    "abs_error": round(abs(obs_freq - pred_freq), 4),
                })

            results[label] = {
                "bins": bin_data,
                "ece": round(sum(
                    b["abs_error"] * b["count"] for b in bin_data
                ) / max(sum(b["count"] for b in bin_data), 1), 4),
                "mce": round(max(
                    (b["abs_error"] for b in bin_data if b["count"] > 0), default=0
                ), 4),
            }

        # Overall ECE/MCE
        overall_ece = np.mean([results[l]["ece"] for l in labels])
        overall_mce = np.max([results[l]["mce"] for l in labels])

        return {
            "per_outcome": results,
            "overall_ece": round(float(overall_ece), 4),
            "overall_mce": round(float(overall_mce), 4),
            "n_bins": self.n_bins,
        }
