import uuid

from pydantic import BaseModel, ConfigDict


class GroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    competition_id: uuid.UUID
    name: str
    stage: str


class GroupStandingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    group_id: uuid.UUID
    team_id: uuid.UUID
    team_name: str
    position: int
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int
    xg_for: float
    xg_against: float
    qualified: bool


class GroupDetail(GroupResponse):
    standings: list[GroupStandingResponse]
