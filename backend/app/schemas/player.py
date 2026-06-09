import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict


class PlayerBase(BaseModel):
    name: str
    position: str | None = None
    shirt_number: int | None = None
    date_of_birth: date | None = None
    market_value: float | None = None
    nationality: str | None = None
    goals: int = 0
    assists: int = 0
    appearances: int = 0


class PlayerCreate(PlayerBase):
    team_id: uuid.UUID


class PlayerResponse(PlayerBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    team_id: uuid.UUID
