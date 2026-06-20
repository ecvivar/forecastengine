"""
Sprint 5 — FASE 2: Dynamic Elo Engine.

Glicko-inspired rating system tracking:
  - rating: point estimate (~1500 baseline)
  - rating_deviation: uncertainty (35-200 range)
  - volatility: how quickly ratings change over time

Lower RD = more confidence in rating.
Higher RD = more uncertainty → wider prediction intervals.
"""
import logging
import math
from dataclasses import dataclass

from app.domain.entities import TeamEntity

logger = logging.getLogger(__name__)


@dataclass
class DynamicEloRating:
    team_id: str
    rating: float = 1500.0
    rd: float = 35.0
    volatility: float = 0.06
    games_played: int = 0


class DynamicEloEngine:
    """
    Dynamic Elo with Glicko-inspired rating deviation.

    Rating updates use scaled K-factor based on RD (higher RD = bigger updates).
    RD increases over time (inactivity) and decreases after matches.
    """

    INITIAL_RATING = 1500
    INITIAL_RD = 35.0
    MIN_RD = 25.0
    MAX_RD = 200.0
    C = 15.0

    def __init__(self, k_factor: float = 32.0):
        self.k_factor = k_factor
        self._ratings: dict[str, DynamicEloRating] = {}

    def get_or_create(self, team_id: str, initial_rating: float = INITIAL_RATING) -> DynamicEloRating:
        if team_id not in self._ratings:
            self._ratings[team_id] = DynamicEloRating(
                team_id=team_id, rating=initial_rating
            )
        return self._ratings[team_id]

    def expected_score(self, rating_a: float, rating_b: float) -> float:
        return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))

    def update_rating(
        self,
        team_id: str,
        opponent_id: str,
        score: float,
        opponent_score: float,
    ) -> DynamicEloRating:
        rating = self.get_or_create(team_id)
        opponent = self.get_or_create(opponent_id)

        expected = self.expected_score(rating.rating, opponent.rating)

        g = 1.0 / math.sqrt(1.0 + 3.0 * (opponent.rd ** 2) / (math.pi ** 2))
        actual = 1.0 if score > opponent_score else (0.5 if score == opponent_score else 0.0)

        d2 = 1.0 / (g ** 2 * expected * (1 - expected))
        k_eff = self.k_factor / (1.0 + rating.rd / 100.0)

        new_rating = rating.rating + k_eff * g * (actual - expected)
        new_rd = max(self.MIN_RD, min(self.MAX_RD,
                     math.sqrt(rating.rd ** 2 + self.C ** 2) / (1.0 + 0.5 * abs(actual - expected))))

        rating.rating = round(new_rating, 1)
        rating.rd = round(new_rd, 1)
        rating.games_played += 1

        return rating

    def predict_outcome(self, home_id: str, away_id: str) -> tuple[float, float]:
        home = self.get_or_create(home_id)
        away = self.get_or_create(away_id)
        expected = self.expected_score(home.rating, away.rating)
        rd_uncertainty = (home.rd + away.rd) / 400.0
        expected_low = max(0.05, expected - rd_uncertainty)
        expected_high = min(0.95, expected + rd_uncertainty)
        return expected_low, expected_high

    def decay_rd(self, team_id: str, days_inactive: int = 1):
        rating = self.get_or_create(team_id)
        rd_increase = self.C * math.sqrt(days_inactive)
        rating.rd = min(self.MAX_RD, rating.rd + rd_increase)

    def to_team_entity(self, team_id: str, team_name: str, base_entity: TeamEntity | None = None) -> TeamEntity:
        dr = self.get_or_create(team_id)
        if base_entity:
            base_entity.elo_score = int(round(dr.rating))
            base_entity.rating_deviation = dr.rd
            base_entity.volatility = dr.volatility
            return base_entity
        import uuid
        return TeamEntity(
            id=uuid.uuid4(), name=team_name,
            elo_score=int(round(dr.rating)),
            rating_deviation=dr.rd, volatility=dr.volatility,
        )
