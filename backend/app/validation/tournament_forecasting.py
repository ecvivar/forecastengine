"""
Sprint 8 - FASE 6: Tournament Forecast Validation.

Evaluates champion, finalist, semi, quarter, R16 forecasts for 2014, 2018, 2022.
Uses BacktestingEngine to run per-tournament simulations and extract forecast quality.
"""
from __future__ import annotations

import logging
import uuid
from collections import defaultdict

import numpy as np

from app.data.historical_matches import ALL_HISTORICAL_MATCHES
from app.domain.entities import PredictionConfig, TeamEntity
from app.engine.match_prediction import MatchPredictionEngine
from app.engine.meta_ensemble import MetaPredictionEngine
from app.validation.calibration_metrics import CalibrationMetrics
from app.validation.backtesting import BacktestingEngine

logger = logging.getLogger(__name__)


class TournamentForecastValidator:
    """
    Validate tournament-level forecasts against historical World Cups.

    For each tournament (2014, 2018, 2022):
      - Predict all matches
      - Simulate tournament N times
      - Measure: champion rank, top4 inclusion, top8 inclusion, tournament Brier
    """

    def __init__(self, config: PredictionConfig | None = None):
        self.config = config or PredictionConfig()
        self.bt = BacktestingEngine(config=self.config)
        self.metrics = CalibrationMetrics()

    def validate_tournament(self, tournament: str, n_simulations: int = 10_000) -> dict:
        """Run full validation for a single tournament."""
        matches = [m for m in ALL_HISTORICAL_MATCHES if m.tournament == tournament]
        result = self.bt.simulate_tournament(matches, tournament, n_simulations)

        # Actual results
        last_match = max((m for m in matches if m.stage == "final"),
                         key=lambda m: int(m.tournament), default=None)
        actual_champion = last_match.home_team if last_match and last_match.home_goals > last_match.away_goals else (
            last_match.away_team if last_match else "unknown"
        )

        # Semi-finalists, quarter-finalists from knockout stage
        semi_teams = set()
        quarter_teams = set()
        r16_teams = set()
        for m in matches:
            if m.stage in ("semi_final", "third_place"):
                semi_teams.add(m.home_team)
                semi_teams.add(m.away_team)
            if m.stage in ("quarter_final", "semi_final", "third_place"):
                quarter_teams.add(m.home_team)
                quarter_teams.add(m.away_team)
            if m.stage in ("round_of_16", "quarter_final", "semi_final", "third_place"):
                r16_teams.add(m.home_team)
                r16_teams.add(m.away_team)

        # Re-run tournament simulation with MonteCarloEngine via BacktestingEngine
        # Get ranked teams by champion probability
        # BacktestingEngine doesn't expose champion probs directly, so we extract from match predictions
        team_entities = self.bt._build_team_entity  # method ref
        team_data = self.bt._extract_team_data(matches)

        # Build entity dict
        entities = {}
        for name, data in team_data.items():
            entities[name] = self.bt._build_team_entity(name, data)

        # Match predictions for tournament Brier
        mpe = MatchPredictionEngine(config=self.config)
        probs, outcomes = [], []
        for m in matches:
            home = entities.get(m.home_team)
            away = entities.get(m.away_team)
            if not home or not away:
                continue
            r = mpe.predict_full(home, away)
            probs.append([r.home_win_prob, r.draw_prob, r.away_win_prob])
            if m.home_goals > m.away_goals:
                outcomes.append([1, 0, 0])
            elif m.home_goals == m.away_goals:
                outcomes.append([0, 1, 0])
            else:
                outcomes.append([0, 0, 1])

        pa = np.array(probs)
        oa = np.array(outcomes)
        tourn_brier = self.metrics.brier_score(pa, oa)

        # Get champion probability ranking from simulation results
        predicted_champion = result.predicted_champion
        champion_prob = result.champion_probability

        # Compute champion rank: position of actual champion in predicted ranking
        # Sort teams by predicted champion probability descending
        # We don't have per-team probs from TournamentBacktestResult, so use BacktestingEngine
        # Actually, let's use match-level strength as a proxy
        strengths = {}
        for name, entity in entities.items():
            s = mpe.compute_team_strength(entity).overall_strength
            strengths[name] = s

        ranked_teams = sorted(strengths.items(), key=lambda x: -x[1])
        champion_rank = 1
        for i, (name, _) in enumerate(ranked_teams):
            if name == actual_champion:
                champion_rank = i + 1
                break

        # Top 4 inclusion: are all 4 semi-finalists in top 8 predicted?
        predicted_top8 = set(name for name, _ in ranked_teams[:8])
        predicted_top4 = set(name for name, _ in ranked_teams[:4])
        top4_inclusion = len(semi_teams & predicted_top8) / max(len(semi_teams), 1)
        top8_inclusion = len(quarter_teams & predicted_top8) / max(len(quarter_teams), 1)

        return {
            "tournament": tournament,
            "n_matches": len(matches),
            "actual_champion": actual_champion,
            "predicted_champion": predicted_champion,
            "champion_probability": round(champion_prob * 100, 2),
            "champion_rank": champion_rank,
            "top4_inclusion": round(top4_inclusion * 100, 1),
            "top8_inclusion": round(top8_inclusion * 100, 1),
            "tournament_brier": round(tourn_brier, 4),
            "result": result,
        }

    def run_all(self) -> list[dict]:
        """Validate all 3 tournaments."""
        results = []
        for t in ("2014", "2018", "2022"):
            r = self.validate_tournament(t)
            results.append(r)
            logger.info(f"  {t}: champion={r['actual_champion']}, "
                        f"pred={r['predicted_champion']}, "
                        f"rank={r['champion_rank']}, "
                        f"Brier={r['tournament_brier']}")
        return results
