"""
FASE 1 — Elo Variance Decomposition.

Measures dP/dElo, local elasticity, global elasticity, and impact by Elo range.
Segments: <1500, 1500-1650, 1650-1800, 1800-1950, >1950
"""
from __future__ import annotations

import logging
from copy import deepcopy

import numpy as np

from app.domain.entities import PredictionConfig
from app.engine.match_prediction import MatchPredictionEngine

logger = logging.getLogger(__name__)


class EloSensitivityAnalyzer:
    """Decompose Elo sensitivity by range and magnitude."""

    ELO_RANGES = [
        ("<1500", 0, 1500),
        ("1500-1650", 1500, 1650),
        ("1650-1800", 1650, 1800),
        ("1800-1950", 1800, 1950),
        (">1950", 1950, 9999),
    ]

    def __init__(self, config: PredictionConfig | None = None):
        self.config = config or PredictionConfig()
        self.engine = MatchPredictionEngine(config=self.config)

    def analyze_single(self, home, away, delta: int = 50) -> dict:
        """Compute dP/dElo for a single match pair."""
        baseline = self.engine.predict_full(home, away)
        base_hw = baseline.home_win_prob

        h_up = deepcopy(home)
        h_up.elo_score = min(2500, home.elo_score + delta)
        r_up = self.engine.predict_full(h_up, away)
        dp_delo_up = (r_up.home_win_prob - base_hw) / max(delta, 1)

        h_down = deepcopy(home)
        h_down.elo_score = max(1000, home.elo_score - delta)
        r_down = self.engine.predict_full(h_down, away)
        dp_delo_down = (base_hw - r_down.home_win_prob) / max(delta, 1)

        avg_dp_delo = (dp_delo_up + dp_delo_down) / 2.0
        elasticity = avg_dp_delo * (home.elo_score / max(base_hw, 0.001))

        return {
            "home_elo": home.elo_score,
            "base_hw": round(base_hw, 4),
            "dp_delo_up": round(dp_delo_up, 6),
            "dp_delo_down": round(dp_delo_down, 6),
            "avg_dp_delo": round(avg_dp_delo, 6),
            "local_elasticity": round(elasticity, 4),
            "elo_range": self._get_range(home.elo_score),
        }

    def _get_range(self, elo: int) -> str:
        for label, lo, hi in self.ELO_RANGES:
            if lo <= elo < hi:
                return label
        return ">1950"

    def analyze_all(self, match_pairs: list[tuple], delta: int = 50) -> dict:
        """Aggregate sensitivity by Elo range across all matches."""
        by_range = {label: [] for label, _, _ in self.ELO_RANGES}

        for home, away, _outcome in match_pairs:
            result = self.analyze_single(home, away, delta)
            r = result["elo_range"]
            by_range[r].append(result)

        summary = {}
        for label, items in by_range.items():
            if not items:
                summary[label] = {"count": 0, "mean_dp_delo": 0, "mean_elasticity": 0}
                continue
            dp = np.mean([i["avg_dp_delo"] for i in items])
            el = np.mean([i["local_elasticity"] for i in items])
            summary[label] = {
                "count": len(items),
                "mean_dp_delo": round(float(dp), 6),
                "mean_elasticity": round(float(el), 4),
                "median_dp_delo": round(float(np.median([i["avg_dp_delo"] for i in items])), 6),
                "std_dp_delo": round(float(np.std([i["avg_dp_delo"] for i in items])), 6),
            }

        global_dp = np.mean([i["avg_dp_delo"] for results in by_range.values() for i in results])
        global_el = np.mean([i["local_elasticity"] for results in by_range.values() for i in results])

        return {
            "by_range": summary,
            "global_mean_dp_delo": round(float(global_dp), 6),
            "global_mean_elasticity": round(float(global_el), 4),
        }
