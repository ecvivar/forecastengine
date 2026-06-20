"""
Sprint 3 — FASE 3: Automatic Weight Optimization.

Grid search over elo, xg_attack, xg_defense, fifa weights to minimize
log loss and Brier score against historical World Cup matches.

Constraints:
  - Sum of weights = 1.0
  - elo: 0.20-0.60, xg_attack: 0.10-0.40, xg_defense: 0.10-0.30, fifa: 0.00-0.20
  - Does NOT modify production config automatically.
"""

import itertools
import logging

import numpy as np

from app.data.historical_matches import ALL_HISTORICAL_MATCHES
from app.domain.entities import PredictionConfig, TeamEntity
from app.engine.match_prediction import MatchPredictionEngine
from app.validation.calibration_metrics import CalibrationMetrics

logger = logging.getLogger(__name__)


class WeightOptimizer:
    """Grid search over PredictionConfig weights to find optimal mix."""

    ELOS = (0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60)
    XG_ATTACKS = (0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40)
    XG_DEFENSES = (0.10, 0.15, 0.20, 0.25, 0.30)
    FIFAS = (0.00, 0.05, 0.10, 0.15, 0.20)

    # Remaining weight after elo + xg_atk + xg_def must be filled by fifa
    # We only generate valid combinations where fifa = 1.0 - elo - xg_atk - xg_def
    # and fifa is in FIFAS.

    def __init__(self):
        self.metrics = CalibrationMetrics()
        self._build_team_cache()

    def _build_team_cache(self):
        """Build a cache of TeamEntity for each team from historical data."""
        from app.validation.backtesting import BacktestingEngine

        backtester = BacktestingEngine()
        self._team_cache: dict[str, dict[str, TeamEntity]] = {}
        self._match_data: dict[str, list] = {}

        for tournament in ("2014", "2018", "2022"):
            matches = [m for m in ALL_HISTORICAL_MATCHES if m.tournament == tournament]
            team_data = backtester._extract_team_data(matches)
            self._team_cache[tournament] = {
                name: backtester._build_team_entity(name, d)
                for name, d in team_data.items()
            }
            self._match_data[tournament] = matches

    def _all_matches(self) -> list[tuple[TeamEntity, TeamEntity, np.ndarray]]:
        """Return all historical matches as (home, away, outcome_onehot)."""
        pairs = []
        outcome_map = {"home": 0, "draw": 1, "away": 2}
        for tournament in ("2014", "2018", "2022"):
            teams = self._team_cache[tournament]
            for m in self._match_data[tournament]:
                home = teams.get(m.home_team)
                away = teams.get(m.away_team)
                if not home or not away:
                    continue
                if m.home_goals > m.away_goals:
                    outcome = np.array([1, 0, 0])
                elif m.home_goals == m.away_goals:
                    outcome = np.array([0, 1, 0])
                else:
                    outcome = np.array([0, 0, 1])
                pairs.append((home, away, outcome))
        return pairs

    def _score_weights(
        self, elo: float, xg_atk: float, xg_def: float, fifa: float
    ) -> dict:
        """Compute metrics for a given weight combination."""
        config = PredictionConfig(
            elo_weight=elo,
            xg_attack_weight=xg_atk,
            xg_defense_weight=xg_def,
            fifa_weight=fifa,
        )
        engine = MatchPredictionEngine(config=config)

        probs = []
        outcomes = []

        for home, away, outcome in self._all_matches():
            r = engine.predict_full(home, away, home_advantage=True)
            probs.append([r.home_win_prob, r.draw_prob, r.away_win_prob])
            outcomes.append(outcome)

        if not probs:
            return {"brier": 999, "log_loss": 999, "count": 0}

        probs_arr = np.array(probs)
        outcomes_arr = np.array(outcomes)
        return {
            "brier": round(self.metrics.brier_score(probs_arr, outcomes_arr), 6),
            "log_loss": round(self.metrics.log_loss(probs_arr, outcomes_arr), 6),
            "count": len(probs),
        }

    def search(self) -> dict:
        """
        Exhaustive grid search over all valid weight combinations.
        
        Returns:
            dict with best_weights, best_metrics, all_results
        """
        candidates = []
        step = 0
        total_steps = (
            len(self.ELOS)
            * len(self.XG_ATTACKS)
            * len(self.XG_DEFENSES)
            * len(self.FIFAS)
        )

        for elo in self.ELOS:
            for xg_atk in self.XG_ATTACKS:
                for xg_def in self.XG_DEFENSES:
                    for fifa in self.FIFAS:
                        step += 1
                        if abs((elo + xg_atk + xg_def + fifa) - 1.0) > 0.001:
                            continue

                        metrics = self._score_weights(elo, xg_atk, xg_def, fifa)
                        entry = {
                            "weights": {
                                "elo": round(elo, 2),
                                "xg_attack": round(xg_atk, 2),
                                "xg_defense": round(xg_def, 2),
                                "fifa": round(fifa, 2),
                            },
                            **metrics,
                        }
                        candidates.append(entry)

                        if step % 50 == 0 or step == total_steps:
                            logger.info(
                                f"Grid search {step}/{total_steps}: "
                                f"elo={elo} xg_atk={xg_atk} xg_def={xg_def} fifa={fifa}"
                            )

        # Find best by log_loss (primary) and brier (secondary)
        valid = [c for c in candidates if c["count"] > 0]
        if not valid:
            return {"best_weights": None, "best_metrics": None, "results": []}

        best = min(valid, key=lambda c: (c["log_loss"], c["brier"]))
        current = PredictionConfig()
        current_w = {
            "elo": current.elo_weight,
            "xg_attack": current.xg_attack_weight,
            "xg_defense": current.xg_defense_weight,
            "fifa": current.fifa_weight,
        }

        # Find current weight position in ranking
        sorted_all = sorted(valid, key=lambda c: (c["log_loss"], c["brier"]))
        current_metrics = self._score_weights(
            current.elo_weight,
            current.xg_attack_weight,
            current.xg_defense_weight,
            current.fifa_weight,
        )

        return {
            "best_weights": best["weights"],
            "best_metrics": {
                "brier": best["brier"],
                "log_loss": best["log_loss"],
            },
            "current_weights": current_w,
            "current_metrics": current_metrics,
            "improvement": {
                "brier_delta": round(current_metrics["brier"] - best["brier"], 6),
                "log_loss_delta": round(current_metrics["log_loss"] - best["log_loss"], 6),
            },
            "n_candidates": len(valid),
            "results": sorted_all,
        }
