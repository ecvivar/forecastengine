"""
Domain Entities for WorldCup Forecast Engine 2026.

Pure domain objects following DDD — no ORM dependencies.
"""

"""
Domain Entities for WorldCup Forecast Engine 2026.

Sprint 5 additions:
  - TeamStrength: attack_rating, defense_rating, overall_rating, uncertainty
  - TeamEntity: rating_deviation, volatility (for Dynamic Elo)
  - TournamentUncertainty: CI for champion/finalist/semi
  - ScenarioConfig: injury/red_card/suspension/form modifications
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
    xg_for: float | None = None
    xg_against: float | None = None
    rating_deviation: float = 35.0
    volatility: float = 0.06


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
    ci_90: dict | None = None


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
class TeamStrength:
    attack_strength: float = 1.0
    defense_strength: float = 1.0
    overall_strength: float = 1.0
    attack_rating: float = 1.0
    defense_rating: float = 1.0
    overall_rating: float = 1.0
    uncertainty: float = 0.0


@dataclass
class PredictionConfig:
    elo_weight: float = 0.40
    xg_attack_weight: float = 0.30
    xg_defense_weight: float = 0.20
    fifa_weight: float = 0.10
    home_advantage: float = 0.08
    dixon_coles_tau: float = 0.1
    bayesian_prior_strength: float = 0.5
    max_goals: int = 10
    league_avg_goals: float = 1.25
    top_n_scores: int = 10
    calibration_adjustments: dict | None = None
    ensemble_weights: dict | None = None


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
class TournamentUncertainty:
    team_id: uuid.UUID
    team_name: str
    win_probability: float
    variance: float
    std_dev: float
    ci_90: tuple[float, float]


@dataclass
class BracketNode:
    round_name: str
    matches: list[tuple[int | None, int | None]] = field(default_factory=list)
    winners: list[int | None] = field(default_factory=list)


@dataclass
class ScenarioConfig:
    injury: list[str] | None = None
    red_card: list[str] | None = None
    suspension: list[str] | None = None
    form_drop: dict[str, float] | None = None
    form_boost: dict[str, float] | None = None
