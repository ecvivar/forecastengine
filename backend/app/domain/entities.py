"""
Domain Entities for WorldCup Forecast Engine 2026.

Pure domain objects following DDD — no ORM dependencies.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any
import uuid


class MatchStage(str, Enum):
    GROUP_STAGE = "group_stage"
    ROUND_OF_32 = "round_of_32"
    ROUND_OF_16 = "round_of_16"
    QUARTER_FINAL = "quarter_final"
    SEMI_FINAL = "semi_final"
    THIRD_PLACE = "third_place"
    FINAL = "final"


class MatchStatus(str, Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"
    POSTPONED = "postponed"


class ConfidenceLevel(str, Enum):
    MUY_ALTA = "Muy Alta"
    ALTA = "Alta"
    MEDIA = "Media"
    BAJA = "Baja"
    MUY_BAJA = "Muy Baja"


@dataclass
class TeamEntity:
    id: uuid.UUID
    name: str
    fifa_code: str | None = None
    continent: str | None = None
    elo_score: int = 1500
    fifa_rank: int | None = None
    igf_score: float = 0.0


@dataclass
class PlayerEntity:
    id: uuid.UUID
    team_id: uuid.UUID
    name: str
    position: str | None = None
    market_value: float | None = None


@dataclass
class MatchEntity:
    id: uuid.UUID
    competition_id: uuid.UUID
    home_team_id: uuid.UUID
    away_team_id: uuid.UUID
    home_team: str
    away_team: str
    match_date: datetime
    stage: MatchStage
    group_name: str | None = None
    home_goals: int | None = None
    away_goals: int | None = None
    home_xg: float | None = None
    away_xg: float | None = None
    is_neutral: bool = False
    status: MatchStatus = MatchStatus.SCHEDULED


@dataclass
class MatchPredictionResult:
    match_id: uuid.UUID
    home_team: str
    away_team: str
    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    home_expected_goals: float
    away_expected_goals: float
    most_likely_score: str
    score_probabilities: dict[str, float] = field(default_factory=dict)
    top_10_scores: list[tuple[str, float]] = field(default_factory=list)
    confidence_index: float = 0.0
    confidence_level: str = "Media"
    surprise_risk: float = 0.0
    btts_prob: float = 0.0
    over_25_prob: float = 0.0
    over_35_prob: float = 0.0
    under_25_prob: float = 0.0
    home_clean_sheet: float = 0.0
    away_clean_sheet: float = 0.0


@dataclass
class GroupStandingEntity:
    team_id: uuid.UUID
    team_name: str
    group_name: str
    position: int = 0
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0
    goal_difference: int = 0
    points: int = 0
    points_deduted: int = 0
    head_to_head_points: int = 0
    head_to_head_gd: int = 0
    head_to_head_gf: int = 0


@dataclass
class GroupAnalysis:
    group_name: str
    teams: list[GroupStandingEntity]
    competitiveness_index: float
    strength_range: float
    favorite_id: uuid.UUID
    outsider_id: uuid.UUID
    surprise_risk: float


@dataclass
class SimulationConfig:
    num_simulations: int = 100_000
    random_seed: int | None = None
    use_numba: bool = True
    parallel: bool = True


@dataclass
class TournamentResult:
    team_id: uuid.UUID
    team_name: str
    group_name: str
    group_position: int = 0
    group_points: float = 0.0
    group_gd: float = 0.0
    round_of_32_count: int = 0
    round_of_16_count: int = 0
    quarter_final_count: int = 0
    semi_final_count: int = 0
    final_count: int = 0
    won_count: int = 0
    total_points: float = 0.0
    pos1_count: int = 0
    pos2_count: int = 0
    pos3_count: int = 0
    pos4_count: int = 0


@dataclass
class BracketNode:
    round_name: str
    matches: list[tuple[int | None, int | None]] = field(default_factory=list)
    winners: list[int | None] = field(default_factory=list)
