"""
Sprint 3 — FASE 7: Tournament Explainability Engine.

Explains each team's champion probability by decomposing it into
per-signal contributions (elo, xg, fifa, home_advantage, other).

Uses the `overall_strength` formula from MatchPredictionEngine, because
Monte Carlo uses overall_strength for tournament simulation.

Every percentage is computed from real weights, not hardcoded.
"""

import logging
from copy import deepcopy

import numpy as np

from app.domain.entities import PredictionConfig, TeamEntity, TeamStrength
from app.engine.match_prediction import MatchPredictionEngine

logger = logging.getLogger(__name__)


class TournamentExplainabilityEngine:
    """
    Explains tournament-level champion probabilities by computing
    the contribution of each signal to each team's overall_strength.
    
    The Monte Carlo engine uses overall_strength directly for simulation.
    Each signal (elo, xg_attack, xg_defense, fifa) contributes to 
    overall_strength via the composite formula:
    
      overall_strength = (w_elo * elo_norm + w_xg_atk * attack_xg
                         + w_xg_def * defense_xg + w_fifa * fifa_norm)
                        / total_weight
    
    The contribution of each signal is its weighted share of the final
    overall_strength.
    """

    def __init__(self, config: PredictionConfig | None = None):
        self.config = config or PredictionConfig()
        self.engine = MatchPredictionEngine(config=self.config)

    def explain_team(self, team: TeamEntity) -> dict:
        """
        Explain the contribution of each signal to a team's overall_strength.
        
        Returns:
            dict with overall_strength and per-signal breakdown
        """
        ts = self.engine.compute_team_strength(team)
        overall = ts.overall_strength

        # Decompose overall_strength into per-signal contributions
        # overall = (w_elo * elo_norm + w_xg_atk * atk + w_xg_def * def + w_fifa * fifa) / total_w
        w = self.config
        total_w = w.elo_weight + w.xg_attack_weight + w.xg_defense_weight + w.fifa_weight
        total_w = max(total_w, 0.001)

        elo_norm = team.elo_score / 1500.0
        rank = team.fifa_rank or 100
        fifa_norm = max(0.7, min(1.3, 100.0 / rank))

        # xG components (same as MatchPredictionEngine._compute_team_strength)
        if team.xg_for is not None and team.xg_for > 0:
            attack_xg = team.xg_for / 1.5
            attack_xg = max(0.3, min(3.0, attack_xg))
        else:
            attack_xg = 1.0

        if team.xg_against is not None and team.xg_against > 0:
            defense_xg = 1.5 / team.xg_against
            defense_xg = max(0.3, min(3.0, defense_xg))
        else:
            defense_xg = 1.0

        # Per-signal weighted contributions to overall_strength
        contrib_elo = (w.elo_weight * elo_norm) / total_w
        contrib_xg_atk = (w.xg_attack_weight * attack_xg) / total_w
        contrib_xg_def = (w.xg_defense_weight * defense_xg) / total_w
        contrib_fifa = (w.fifa_weight * fifa_norm) / total_w

        total_contrib = contrib_elo + contrib_xg_atk + contrib_xg_def + contrib_fifa

        if total_contrib > 0:
            pct_elo = contrib_elo / total_contrib * 100
            pct_xg_atk = contrib_xg_atk / total_contrib * 100
            pct_xg_def = contrib_xg_def / total_contrib * 100
            pct_fifa = contrib_fifa / total_contrib * 100
        else:
            pct_elo = pct_xg_atk = pct_xg_def = pct_fifa = 0.0

        # Aggregate xG
        pct_xg = pct_xg_atk + pct_xg_def

        # "other" = residual (home_advantage is not in overall_strength)
        # home_advantage only affects match-level Poisson lambda, not overall_strength
        residual = max(0.0, 100.0 - pct_elo - pct_xg - pct_fifa)

        return {
            "team": team.name,
            "overall_strength": round(overall, 4),
            "drivers": {
                "elo": round(pct_elo, 1),
                "xg": round(pct_xg, 1),
                "xg_attack": round(pct_xg_atk, 1),
                "xg_defense": round(pct_xg_def, 1),
                "fifa": round(pct_fifa, 1),
                "other": round(residual, 1),
            },
            "raw_components": {
                "elo_norm": round(elo_norm, 4),
                "attack_xg": round(attack_xg, 4),
                "defense_xg": round(defense_xg, 4),
                "fifa_norm": round(fifa_norm, 4),
            },
            "weights": {
                "elo": w.elo_weight,
                "xg_attack": w.xg_attack_weight,
                "xg_defense": w.xg_defense_weight,
                "fifa": w.fifa_weight,
            },
        }

    def explain_all_teams(self, teams: list[TeamEntity]) -> list[dict]:
        """Explain signals for multiple teams."""
        return [self.explain_team(t) for t in teams]

    def summarize_tournament(self, teams: list[TeamEntity]) -> dict:
        """Summarize signal importance across all tournament teams."""
        explanations = self.explain_all_teams(teams)
        if not explanations:
            return {}

        # Top-level drivers only (elo, xg, fifa, other) — avoid double-counting
        # xg_attack + xg_defense = xg, so only include the aggregate
        top_level = ["elo", "xg", "fifa", "other"]
        avg_drivers = {}
        for key in top_level:
            if key in explanations[0]["drivers"]:
                avg_drivers[key] = round(
                    np.mean([e["drivers"][key] for e in explanations]), 1
                )

        return {
            "teams": explanations,
            "average_drivers": avg_drivers,
            "sum_check": round(sum(avg_drivers.values()), 1),
            "config": {
                "elo_weight": self.config.elo_weight,
                "xg_attack_weight": self.config.xg_attack_weight,
                "xg_defense_weight": self.config.xg_defense_weight,
                "fifa_weight": self.config.fifa_weight,
                "home_advantage": self.config.home_advantage,
                "bayesian_prior_strength": self.config.bayesian_prior_strength,
            },
        }
