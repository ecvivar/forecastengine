import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict


class CompetitionBase(BaseModel):
    name: str
    season: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    competition_type: str = "world_cup"
    format: str = "group_plus_knockout"


class CompetitionCreate(CompetitionBase):
    pass


class CompetitionResponse(CompetitionBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
