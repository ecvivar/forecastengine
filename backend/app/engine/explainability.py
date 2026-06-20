"""
Sprint 3 — FASE 5: Explainability Engine.

Decomposes a match prediction into per-signal driver contributions.
All drivers are computed from real deltas (ablation approach), not hardcoded.

Architecture:
  Full prediction → disable one signal → measure delta in home_win_prob
  → normalize to sum ≈ 100%
"""

import logging
from copy import deepcopy

from app.domain.entities import (
    MatchPredictionResult,
    PredictionConfig,
    TeamEntity,
    TeamStrength,
)
from app.engine.match_prediction import MatchPredictionEngine

logger = logging.getLogger(__name__)


class MatchExplanation:
    """
    Explanation of a single match prediction with per-signal driver breakdown.

    Drivers: elo, xg_attack, xg_defense, fifa, home_advantage
    All drivers sum to approximately 100%.
    """

    def __init__(
        self,
        prediction: MatchPredictionResult,
        drivers: dict[str, float],
    ):
        self.prediction = prediction
        self.drivers = drivers

    def to_dict(self) -> dict:
        return {
            "prediction": {
                "home_win": round(self.prediction.home_win_prob, 4),
                "draw": round(self.prediction.draw_prob, 4),
                "away_win": round(self.prediction.away_win_prob, 4),
                "home_expected_goals": self.prediction.home_expected_goals,
                "away_expected_goals": self.prediction.away_expected_goals,
                "most_likely_score": self.prediction.most_likely_score,
                "confidence_index": self.prediction.confidence_index,
                "confidence_level": self.prediction.confidence_level,
            },
            "drivers": {
                k: round(v, 4) for k, v in sorted(
                    self.drivers.items(), key=lambda x: x[1], reverse=True
                )
            },
        }


class ExplainabilityEngine:
    """
    Computes per-signal driver contributions for a match prediction.

    Uses ablation: runs the engine with and without each signal,
    measures the delta in home_win_prob, and normalizes.
    """

    def __init__(self, config: PredictionConfig | None = None):
        self.config = config or PredictionConfig()
        self.engine = MatchPredictionEngine(config=self.config)

    def explain(
        self,
        home_team: TeamEntity,
        away_team: TeamEntity,
        home_advantage: bool = True,
    ) -> MatchExplanation:
        """
        Explain a match prediction by measuring each driver's contribution.
        
        Steps:
          1. Full prediction (baseline)
          2. For each driver: run prediction with that signal neutralized
          3. Compute absolute delta in home_win_prob
          4. Normalize to sum ≈ 1.0
        """
        full = self.engine.predict_full(home_team, away_team, home_advantage)
        baseline_hw = full.home_win_prob

        # ── Compute per-driver deltas ──
        raw_drivers = {}

        # Elo: neutralize Bayesian prior (set prior strength to 0)
        cfg_no_elo = deepcopy(self.config)
        cfg_no_elo.bayesian_prior_strength = 0.0
        engine_no_elo = MatchPredictionEngine(config=cfg_no_elo)
        no_elo = engine_no_elo.predict_full(home_team, away_team, home_advantage)
        raw_drivers["elo"] = abs(baseline_hw - no_elo.home_win_prob)

        # xG Attack: set xg_for to None (falls back to 1.0)
        home_no_xg_atk = deepcopy(home_team)
        away_no_xg_atk = deepcopy(away_team)
        home_no_xg_atk.xg_for = None
        away_no_xg_atk.xg_for = None
        no_xg_atk = self.engine.predict_full(home_no_xg_atk, away_no_xg_atk, home_advantage)
        raw_drivers["xg_attack"] = abs(baseline_hw - no_xg_atk.home_win_prob)

        # xG Defense: set xg_against to None (falls back to 1.0)
        home_no_xg_def = deepcopy(home_team)
        away_no_xg_def = deepcopy(away_team)
        home_no_xg_def.xg_against = None
        away_no_xg_def.xg_against = None
        no_xg_def = self.engine.predict_full(home_no_xg_def, away_no_xg_def, home_advantage)
        raw_drivers["xg_defense"] = abs(baseline_hw - no_xg_def.home_win_prob)

        # FIFA: set fifa_rank to 100 (median), affects attack/defense composites
        # Since Sprint 4A, FIFA is integrated into attack_strength and
        # defense_strength via the weighted composite formula, so it now
        # produces a real non-zero delta in match-level predictions.
        home_no_fifa = deepcopy(home_team)
        away_no_fifa = deepcopy(away_team)
        home_no_fifa.fifa_rank = 100
        away_no_fifa.fifa_rank = 100
        no_fifa = self.engine.predict_full(home_no_fifa, away_no_fifa, home_advantage)
        raw_drivers["fifa"] = abs(baseline_hw - no_fifa.home_win_prob)

        # Home Advantage: run as neutral
        no_ha = self.engine.predict_full(home_team, away_team, home_advantage=False)
        raw_drivers["home_advantage"] = abs(baseline_hw - no_ha.home_win_prob)

        # ── Dixon-Coles: set tau to 0
        cfg_no_dc = deepcopy(self.config)
        cfg_no_dc.dixon_coles_tau = 0.0
        engine_no_dc = MatchPredictionEngine(config=cfg_no_dc)
        no_dc = engine_no_dc.predict_full(home_team, away_team, home_advantage)
        raw_drivers["dixon_coles"] = abs(baseline_hw - no_dc.home_win_prob)

        # ── Normalize to sum ≈ 100% ──
        # Use the delta from each signal. Normalize by total delta so
        # the sum of all drivers = 1.0 (or close to it).
        total_delta = sum(raw_drivers.values())
        if total_delta > 0:
            drivers = {k: v / total_delta for k, v in raw_drivers.items()}
        else:
            # All signals neutral → drivers are equal
            n = len(raw_drivers)
            drivers = {k: 1.0 / n for k in raw_drivers}

        return MatchExplanation(prediction=full, drivers=drivers)
