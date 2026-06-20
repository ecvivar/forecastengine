"""
FASE 1 — Sensitivity Decomposition.

Measures elasticity of each input variable by applying ±1%, ±5%, ±10%, ±25%
perturbations and measuring Δ home_win, Δ draw, Δ away_win.
"""
from __future__ import annotations

import logging
from copy import deepcopy
from dataclasses import dataclass, field

import numpy as np

from app.domain.entities import PredictionConfig
from app.engine.match_prediction import MatchPredictionEngine

logger = logging.getLogger(__name__)


@dataclass
class SensitivityResult:
    variable: str
    elasticity: float
    sensitivity_score: float
    response_curve: dict[str, dict[str, float]]
    mean_abs_delta: float


class SensitivityDecomposition:
    """Compute per-variable elasticity and sensitivity."""

    PERTURBATIONS = [0.01, 0.05, 0.10, 0.25]  # ±1%, 5%, 10%, 25%

    def __init__(self, config: PredictionConfig | None = None):
        self.config = config or PredictionConfig()
        self.engine = MatchPredictionEngine(config=self.config)

    def analyze(self, home, away, home_advantage: bool = True) -> list[SensitivityResult]:
        baseline = self.engine.predict_full(home, away, home_advantage)
        base_vec = np.array([baseline.home_win_prob, baseline.draw_prob, baseline.away_win_prob])

        results = []
        for var in ["elo", "xg_for", "xg_against", "fifa_rank", "home_advantage"]:
            response_curve = {}
            deltas = []

            for pct in self.PERTURBATIONS:
                for direction, label in [(1, f"+{pct*100:.0f}%"), (-1, f"-{pct*100:.0f}%")]:
                    h = deepcopy(home)
                    a = deepcopy(away)
                    ha = home_advantage

                    if var == "elo":
                        delta = int(h.elo_score * pct * direction)
                        h.elo_score = max(1000, h.elo_score + delta)
                    elif var == "xg_for":
                        h.xg_for = (h.xg_for or 1.5) * (1 + pct * direction)
                    elif var == "xg_against":
                        h.xg_against = (h.xg_against or 1.5) * (1 + pct * direction)
                    elif var == "fifa_rank":
                        delta = max(1, int((h.fifa_rank or 100) * pct * direction))
                        h.fifa_rank = max(1, (h.fifa_rank or 100) - delta)
                    elif var == "home_advantage":
                        ha = direction > 0

                    r = self.engine.predict_full(h, a, ha)
                    perturbed = np.array([r.home_win_prob, r.draw_prob, r.away_win_prob])
                    delta_vec = perturbed - base_vec
                    deltas.append(np.abs(delta_vec))
                    response_curve[label] = {
                        "home_win": round(r.home_win_prob, 4),
                        "draw": round(r.draw_prob, 4),
                        "away_win": round(r.away_win_prob, 4),
                        "delta_hw": round(float(delta_vec[0]), 4),
                        "delta_draw": round(float(delta_vec[1]), 4),
                        "delta_aw": round(float(delta_vec[2]), 4),
                    }

            # Sensitivity score = mean absolute delta across all perturbations
            mean_abs = float(np.mean([np.mean(d) for d in deltas]))
            # Elasticity = mean_abs_delta / mean perturbation magnitude
            mean_perturb = float(np.mean(self.PERTURBATIONS))
            elasticity = mean_abs / max(mean_perturb, 1e-6)

            results.append(SensitivityResult(
                variable=var,
                elasticity=round(elasticity, 4),
                sensitivity_score=round(mean_abs * 100, 2),
                response_curve=response_curve,
                mean_abs_delta=round(mean_abs, 6),
            ))

        return results

    def analyze_all_matches(self, match_pairs: list[tuple]) -> dict:
        """Aggregate sensitivity across many matches."""
        all_scores = {v: [] for v in ["elo", "xg_for", "xg_against", "fifa_rank", "home_advantage"]}

        for home, away, _outcome in match_pairs:
            results = self.analyze(home, away)
            for r in results:
                all_scores[r.variable].append(r.sensitivity_score)

        summary = {}
        for var, scores in all_scores.items():
            scores_arr = np.array(scores)
            summary[var] = {
                "mean_sensitivity": round(float(np.mean(scores_arr)), 4),
                "std_sensitivity": round(float(np.std(scores_arr)), 4),
                "max_sensitivity": round(float(np.max(scores_arr)), 4),
                "p95_sensitivity": round(float(np.percentile(scores_arr, 95)), 4),
            }
        return summary
