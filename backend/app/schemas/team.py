import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict


class TeamBase(BaseModel):
    name: str
    fifa_code: str | None = None
    flag_url: str | None = None
    continent: str | None = None
    founded_year: int | None = None
    is_national_team: bool = True


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: str | None = None
    fifa_code: str | None = None
    flag_url: str | None = None
    continent: str | None = None
    founded_year: int | None = None
    is_national_team: bool | None = None


class TeamResponse(TeamBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID


class TeamWithStats(TeamResponse):
    elo_score: int | None = None
    fifa_rank: int | None = None
    igf_score: float | None = None
