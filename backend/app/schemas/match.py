import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MatchBase(BaseModel):
    competition_id: uuid.UUID
    home_team_id: uuid.UUID
    away_team_id: uuid.UUID
    match_date: datetime
    stage: str
    group_name: str | None = None
    is_neutral_venue: bool = False


class MatchCreate(MatchBase):
    pass


class MatchResponse(MatchBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    home_goals: int | None = None
    away_goals: int | None = None
    home_xg: float | None = None
    away_xg: float | None = None
    status: str
    home_team_name: str | None = None
    away_team_name: str | None = None


class MatchPrediction(BaseModel):
    match_id: uuid.UUID
    home_team: str
    away_team: str
    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    home_expected_goals: float
    away_expected_goals: float
    most_likely_score: str
    score_probabilities: dict[str, float] | None = None


class FullMatchPrediction(MatchPrediction):
    top_10_scores: list[tuple[str, float]] = []
    confidence_index: float = 0.0
    confidence_level: str = "Media"
    surprise_risk: float = 0.0
    btts_prob: float = 0.0
    over_25_prob: float = 0.0
    under_25_prob: float = 0.0
    over_35_prob: float = 0.0
    home_clean_sheet: float = 0.0
    away_clean_sheet: float = 0.0
