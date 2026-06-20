"""
Sprint 5 — FASE 5 & 7 & 8 & 9 & 10:
  - SharpnessMetrics (entropy, concentration)
  - TournamentUncertaintyEngine (variance, std, CI)
  - ScenarioEngine (injuries, red cards, form changes)
  - StressTester (random perturbations)
  - ExplainabilityEngine v2 (ensemble-aware)
"""
import logging
import random
from copy import deepcopy
from math import exp, log

import numpy as np

from app.domain.entities import (
    MatchPredictionResult, PredictionConfig, ScenarioConfig,
    TeamEntity, TeamStrength, TournamentUncertainty,
)
from app.engine.match_prediction import MatchPredictionEngine
from app.engine.meta_ensemble import MetaPredictionEngine
from app.engine.dynamic_elo import DynamicEloEngine

logger = logging.getLogger(__name__)


class SharpnessMetrics:
    """
    Measures how sharp (confident) predictions are.

    Sharpness = how concentrated predictions are around specific outcomes.
    A well-calibrated model should also be sharp (not just predict 33/33/33).
    """

    @staticmethod
    def entropy(probabilities: np.ndarray) -> np.ndarray:
        """Shannon entropy per prediction (lower = sharper)."""
        p = np.clip(probabilities, 1e-15, 1)
        return -np.sum(p * np.log(p), axis=1)

    @staticmethod
    def average_entropy(probabilities: np.ndarray) -> float:
        return float(np.mean(SharpnessMetrics.entropy(probabilities)))

    @staticmethod
    def max_probability(probabilities: np.ndarray) -> np.ndarray:
        """Max probability per prediction (higher = sharper)."""
        return np.max(probabilities, axis=1)

    @staticmethod
    def average_max_prob(probabilities: np.ndarray) -> float:
        return float(np.mean(SharpnessMetrics.max_probability(probabilities)))

    @staticmethod
    def concentration_ratio(probabilities: np.ndarray, top_k: int = 2) -> np.ndarray:
        """Sum of top-k probabilities per prediction."""
        sorted_p = np.sort(probabilities, axis=1)[:, ::-1]
        return np.sum(sorted_p[:, :top_k], axis=1)

    @staticmethod
    def sharpness_score(probabilities: np.ndarray) -> dict:
        """Composite sharpness report."""
        ent = SharpnessMetrics.entropy(probabilities)
        max_p = SharpnessMetrics.max_probability(probabilities)
        return {
            "avg_entropy": round(float(np.mean(ent)), 4),
            "entropy_std": round(float(np.std(ent)), 4),
            "min_entropy": round(float(np.min(ent)), 4),
            "max_entropy": round(float(np.max(ent)), 4),
            "avg_max_prob": round(float(np.mean(max_p)), 4),
            "max_prob_std": round(float(np.std(max_p)), 4),
            "avg_concentration_top2": round(float(np.mean(
                SharpnessMetrics.concentration_ratio(probabilities, 2))), 4),
            "pct_above_50pct": round(float(np.mean(max_p > 0.5) * 100), 1),
            "pct_above_60pct": round(float(np.mean(max_p > 0.6) * 100), 1),
        }


class TournamentUncertaintyEngine:
    """
    Computes uncertainty for tournament-level predictions.

    Given Monte Carlo sim results, produces variance, std_dev, and CI.
    """

    @staticmethod
    def compute(team_name: str, win_count: int, total_sims: int) -> TournamentUncertainty:
        p = win_count / max(total_sims, 1)
        variance = p * (1 - p) / max(total_sims, 1)
        std_dev = variance ** 0.5
        z = 1.645
        ci_lo = max(0, p - z * std_dev)
        ci_hi = min(1, p + z * std_dev)
        return TournamentUncertainty(
            team_id="",
            team_name=team_name,
            win_probability=round(p * 100, 2),
            variance=round(variance * 10000, 4),
            std_dev=round(std_dev * 100, 2),
            ci_90=(round(ci_lo * 100, 2), round(ci_hi * 100, 2)),
        )


class ScenarioEngine:
    """
    Applies match/team modifications and recomputes predictions.

    Supported scenarios:
      - injury: removes a percentage of offensive/defensive strength
      - red_card: reduces team strength by a factor
      - suspension: similar to red_card
      - form_drop: multiplier on elo/xg
      - form_boost: multiplier on elo/xg
    """

    def __init__(self, config: PredictionConfig | None = None):
        self.config = config or PredictionConfig()
        self.engine = MatchPredictionEngine(config=self.config)

    def apply(self, home_team: TeamEntity, away_team: TeamEntity,
              scenario: ScenarioConfig | None = None,
              home_advantage: bool = True) -> MatchPredictionResult:
        if scenario is None:
            return self.engine.predict_full(home_team, away_team, home_advantage)

        home = deepcopy(home_team)
        away = deepcopy(away_team)

        if scenario.injury:
            for injured in scenario.injury:
                home.xg_for = (home.xg_for or 1.5) * 0.85
                home.xg_against = (home.xg_against or 1.5) * 1.15

        if scenario.red_card:
            for _ in scenario.red_card:
                home.xg_for = (home.xg_for or 1.5) * 0.80
                home.xg_against = (home.xg_against or 1.5) * 1.20
                home.elo_score = int(home.elo_score * 0.90)

        if scenario.suspension:
            for _ in scenario.suspension:
                away.xg_for = (away.xg_for or 1.5) * 0.80
                away.xg_against = (away.xg_against or 1.5) * 1.20
                away.elo_score = int(away.elo_score * 0.90)

        if scenario.form_drop:
            for signal, factor in scenario.form_drop.items():
                if signal == "elo":
                    home.elo_score = int(home.elo_score * (1 - factor))
                elif signal == "xg_for":
                    home.xg_for = (home.xg_for or 1.5) * (1 - factor)
                elif signal == "xg_against":
                    away.xg_against = (away.xg_against or 1.5) * (1 + factor)

        if scenario.form_boost:
            for signal, factor in scenario.form_boost.items():
                if signal == "elo":
                    home.elo_score = int(home.elo_score * (1 + factor))
                elif signal == "xg_for":
                    home.xg_for = (home.xg_for or 1.5) * (1 + factor)
                elif signal == "xg_against":
                    away.xg_against = (away.xg_against or 1.5) * (1 - factor)

        return self.engine.predict_full(home, away, home_advantage)


class StressTester:
    """
    Runs N random scenarios by perturbing signals.
    Measures sensitivity, robustness, stability of predictions.
    """

    def __init__(self, config: PredictionConfig | None = None):
        self.config = config or PredictionConfig()
        self.engine = MatchPredictionEngine(config=self.config)

    def run(self, home_team: TeamEntity, away_team: TeamEntity, n_scenarios: int = 1000) -> dict:
        baseline = self.engine.predict_full(home_team, away_team)
        base_hw = baseline.home_win_prob

        results = []
        for _ in range(n_scenarios):
            home = deepcopy(home_team)
            away = deepcopy(away_team)

            home.elo_score = int(home.elo_score * random.uniform(0.85, 1.15))
            away.elo_score = int(away.elo_score * random.uniform(0.85, 1.15))
            if home.xg_for:
                home.xg_for *= random.uniform(0.80, 1.20)
            if away.xg_for:
                away.xg_for *= random.uniform(0.80, 1.20)
            if home.xg_against:
                home.xg_against *= random.uniform(0.80, 1.20)
            if away.xg_against:
                away.xg_against *= random.uniform(0.80, 1.20)
            if home.fifa_rank:
                home.fifa_rank = max(1, int(home.fifa_rank * random.uniform(0.8, 1.2)))
            if away.fifa_rank:
                away.fifa_rank = max(1, int(away.fifa_rank * random.uniform(0.8, 1.2)))

            r = self.engine.predict_full(home, away)
            results.append(r.home_win_prob)

        arr = np.array(results)
        return {
            "baseline_home_win": round(base_hw, 4),
            "mean": round(float(np.mean(arr)), 4),
            "std": round(float(np.std(arr)), 4),
            "min": round(float(np.min(arr)), 4),
            "max": round(float(np.max(arr)), 4),
            "p5": round(float(np.percentile(arr, 5)), 4),
            "p95": round(float(np.percentile(arr, 95)), 4),
            "sensitivity": round(float(np.std(arr) / max(base_hw, 0.001) * 100), 2),
            "n_scenarios": n_scenarios,
        }


class ExplainabilityEngineV2:
    """
    Sprint 5 — FASE 10: Enhanced explainability for match AND tournament.

    Match level: per-signal driver breakdown (sums to 100%).
    Tournament level: champion probability decomposed by signal + variance share.
    """

    def __init__(self, config: PredictionConfig | None = None):
        self.config = config or PredictionConfig()
        from app.engine.explainability import ExplainabilityEngine
        self._base = ExplainabilityEngine(config=config)

    def explain_match(self, home_team: TeamEntity, away_team: TeamEntity,
                      home_advantage: bool = True) -> dict:
        """Enhanced match explainability."""
        base = self._base.explain(home_team, away_team, home_advantage)
        drivers = {k: round(v * 100, 1) for k, v in base.drivers.items()}
        drivers["sum"] = round(sum(drivers.values()), 1)
        return {
            "prediction": base.to_dict()["prediction"],
            "drivers": drivers,
        }

    def explain_tournament(self, teams: list[TeamEntity], champion_probs: dict[str, float],
                           n_sims: int = 10000) -> dict:
        """
        Tournament-level explainability: decompose champion probability into
        signal contributions + variance.
        """
        strengths = {t.name: self._base.engine.compute_team_strength(t) for t in teams}
        total_uncertainty = max(sum(s.uncertainty for s in strengths.values()), 0.001)

        explanations = {}
        for team in teams:
            ts = strengths[team.name]
            p = champion_probs.get(team.name, 0)
            var_share = ts.uncertainty / total_uncertainty

            # Signal contribution to overall_rating
            w = self.config
            tw = w.elo_weight + w.xg_attack_weight + w.xg_defense_weight + w.fifa_weight
            tw = max(tw, 0.001)
            elo_norm = team.elo_score / 1500.0
            rank = team.fifa_rank or 100
            fifa_norm = max(0.7, min(1.3, 100.0 / rank))
            atk_xg = (team.xg_for or 1.5) / 1.5
            def_xg = 1.5 / (team.xg_against or 1.5)

            contrib_elo = w.elo_weight * elo_norm / tw
            contrib_xg = (w.xg_attack_weight * atk_xg + w.xg_defense_weight * def_xg) / tw
            contrib_fifa = w.fifa_weight * fifa_norm / tw
            total_c = contrib_elo + contrib_xg + contrib_fifa

            explanations[team.name] = {
                "champion_probability": round(p, 2),
                "drivers": {
                    "elo": round(contrib_elo / total_c * 100, 1) if total_c > 0 else 0,
                    "xg": round(contrib_xg / total_c * 100, 1) if total_c > 0 else 0,
                    "fifa": round(contrib_fifa / total_c * 100, 1) if total_c > 0 else 0,
                    "variance": round(var_share * 100, 1),
                },
            }

        avg_drivers = {}
        for key in ["elo", "xg", "fifa", "variance"]:
            avg_drivers[key] = round(
                np.mean([ex["drivers"][key] for ex in explanations.values()]), 1
            )
        avg_drivers["sum"] = round(
            sum(avg_drivers.get(k, 0) for k in ["elo", "xg", "fifa"]), 1
        )

        return {
            "teams": explanations,
            "average_drivers": avg_drivers,
        }
